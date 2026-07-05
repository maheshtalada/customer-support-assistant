"""Retention specialist flow ('retention' spoke, persona 'Ray').

The specialist the hub hands off to when the front-line agent can't close
(haggling, sustained negative sentiment, offers exhausted, explicit human
request). Runs a small SOP negotiation ladder and, on acceptance, applies the
offer behind a SIMULATED supervisor approval (no email in this PoC).

  rung 0 -> best eligible retention offer, framed generously
  rung 1 -> next eligible offer
  rung 2 -> stack a goodwill service-recovery credit (supervisor-approved)
  rung 3 -> final executive save; if still declined -> escalate to human queue"""
from .. import data_store, recommendation_engine
from ..rl import bandit

_GOODWILL_CREDIT_USD = 15
_EXEC_CREDIT_USD = 25


def opening_line(reason):
    reasons = {
        "haggle": "I hear you want a better deal, and I have more room than the "
                  "front-line does.",
        "negative_sentiment": "I'm sorry this has been frustrating — I'll personally "
                              "make sure we sort it out.",
        "offers_exhausted": "Let me take a fresh look — I can access retention offers "
                            "beyond the standard ones.",
        "customer_requested": "You've got me now — a senior specialist. Let's fix this.",
        "voice_cannot_resolve": "I can authorize options the front-line can't. Let me help.",
    }
    return reasons.get(reason, "I'm a senior retention specialist — happy to help.")


def _ladder(cust, declined):
    recs, _ = recommendation_engine.recommend(cust, top_n=3)
    return [r for r in recs if r["offer"]["offer_id"] not in declined]


def handle(state, frame):
    cust = data_store.get_customer(state.customer_id)
    rung = state.slots.get("retention_rung", 0)

    # ── acceptance at any rung -> simulated supervisor approval + apply ──────
    if state.flow_step == "retention_pitch" and (
            frame.intent == "CONFIRM_YES" or frame.entities.get("affirmation")):
        return _close(state, cust)

    # ── decline -> record + advance the ladder ───────────────────────────────
    if state.flow_step == "retention_pitch" and (
            frame.intent in ("CONFIRM_NO", "PROMO_DECLINE", "HAGGLE") or
            frame.entities.get("affirmation") is False):
        pitched = state.slots.get("pitched_offer")
        if pitched:
            state.offers_declined.append(pitched)
            bandit.record_reward(pitched, accepted=False)
        rung += 1
        state.slots["retention_rung"] = rung

    remaining = _ladder(cust, state.offers_declined)

    # rung 2: stack a goodwill credit on top of the best remaining offer
    if rung >= 2 and remaining:
        offer = remaining[0]["offer"]
        state.slots["pitched_offer"] = offer["offer_id"]
        state.slots["stack_credit"] = _GOODWILL_CREDIT_USD
        state.flow_step = "retention_pitch"
        return {"template": f"Here's my best: '{offer['title']}' PLUS a "
                f"${_GOODWILL_CREDIT_USD} goodwill credit for the trouble — I've had "
                "that approved for you. Shall I apply both?",
                "facts": {"offer": offer["title"], "goodwill": f"${_GOODWILL_CREDIT_USD}",
                          "approval": "supervisor-approved (simulated)"}}

    # rung 3+: final executive save, then close gracefully (no human handoff)
    if rung >= 3 or not remaining:
        if state.slots.get("exec_offered"):
            state.resolution_status = "resolved"
            state.flow_step = "resolved"
            return {"template": "No problem at all — I've kept your account exactly as it "
                    "is with no changes, and noted your feedback so we can do better. These "
                    "offers stay on your account, so just say the word anytime and I'll apply "
                    "them instantly.", "facts": {"outcome": "no change, offers held open"}}
        state.slots["exec_offered"] = True
        state.slots["pitched_offer"] = "EXEC-SAVE"
        state.flow_step = "retention_pitch"
        return {"template": f"Let me make a final executive offer: a one-time "
                f"${_EXEC_CREDIT_USD} account credit on top of everything discussed, "
                "approved at my discretion. Can we call it a deal?",
                "facts": {"exec_credit": f"${_EXEC_CREDIT_USD}",
                          "approval": "supervisor-approved (simulated)"}}

    # rung 0/1: pitch the next best eligible offer, generously framed
    offer = remaining[0]["offer"]
    state.slots["pitched_offer"] = offer["offer_id"]
    if offer["offer_id"] not in state.offers_pitched:
        state.offers_pitched.append(offer["offer_id"])
        bandit.record_show(offer["offer_id"])
    state.flow_step = "retention_pitch"
    return {"template": f"I can offer you '{offer['title']}', worth ${offer['value_usd']} "
            f"— {remaining[0]['reason']}. This is a genuine retention rate. Want it?",
            "facts": {"offer": offer["title"], "value": f"${offer['value_usd']}"}}


def _close(state, cust):
    pitched = state.slots.get("pitched_offer")
    stack = state.slots.get("stack_credit", 0)
    if pitched == "EXEC-SAVE":
        state.actions.append({"type": "retention.exec_credit", "status": "SUCCESS",
                              "amount_usd": _EXEC_CREDIT_USD, "approval": "SIMULATED"})
        title = f"${_EXEC_CREDIT_USD} executive credit"
    else:
        offer = data_store.get_offer(pitched)
        state.offer_accepted = pitched
        bandit.record_reward(pitched, accepted=True)
        state.actions.append({"type": "retention.apply_offer", "status": "SUCCESS",
                              "offer_id": pitched, "stack_credit_usd": stack,
                              "approval": "SIMULATED"})
        title = offer["title"] + (f" + ${stack} goodwill credit" if stack else "")
    state.resolution_status = "resolved"
    state.flow_step = "resolved"
    return {"template": f"Wonderful — that's approved and applied: {title}. Thank you for "
            "staying with us; you'll see everything on your next statement.",
            "facts": {"applied": title, "approval": "supervisor-approved (simulated)"}}
