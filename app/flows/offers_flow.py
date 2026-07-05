"""UC-02 Promotions & Recommendations flow (front-line 'billing' spoke).

  idle -> score offers, pitch the top one, ask to apply
       -> accept  -> apply offer (records RL reward), resolved
       -> decline -> record RL reward, pitch the next offer, or hand off if
          the customer is haggling / offers exhausted."""
from .. import data_store, recommendation_engine
from ..rl import bandit


def handle(state, frame):
    cust = data_store.get_customer(state.customer_id)
    state.active_flow = "UC-02"

    # ── accept the currently-pitched offer ───────────────────────────────────
    if state.flow_step == "await_decision" and (
            frame.intent == "CONFIRM_YES" or frame.entities.get("affirmation")):
        oid = state.slots.get("pitched_offer")
        offer = data_store.get_offer(oid)
        bandit.record_reward(oid, accepted=True)      # M5 feedback loop
        state.offer_accepted = oid
        state.actions.append({"type": "promotion.apply_offer", "status": "SUCCESS",
                              "offer_id": oid})
        state.resolution_status = "resolved"
        state.flow_step = "resolved"
        return {"template": f"Great choice — I've applied '{offer['title']}' to your "
                f"account. You'll see it on your next bill.",
                "facts": {"offer": offer["title"], "value": f"${offer['value_usd']}"}}

    # ── decline -> record reward, try the next offer or hand off ─────────────
    if state.flow_step == "await_decision" and (
            frame.intent in ("CONFIRM_NO", "PROMO_DECLINE") or
            frame.entities.get("affirmation") is False):
        declined = state.slots.get("pitched_offer")
        if declined:
            state.offers_declined.append(declined)
            bandit.record_reward(declined, accepted=False)   # M5 feedback loop

    # ── pitch the next best eligible, not-yet-declined offer ─────────────────
    recs, _ = recommendation_engine.recommend(cust, top_n=3)
    remaining = [r for r in recs if r["offer"]["offer_id"] not in state.offers_declined]
    if not remaining:
        # offers exhausted -> let the coordinator escalate to retention
        state.flow_step = "await_decision"
        return {"template": "Those were the offers I can extend from here. Let me bring "
                "in our retention specialist to see what else is possible.",
                "facts": {}, "request_handoff": "offers_exhausted"}

    top = remaining[0]
    offer = top["offer"]
    state.slots["pitched_offer"] = offer["offer_id"]
    state.flow_step = "await_decision"
    if offer["offer_id"] not in state.offers_pitched:
        state.offers_pitched.append(offer["offer_id"])
        bandit.record_show(offer["offer_id"])           # M5 show count
    return {
        "template": f"Based on your account, my top recommendation is '{offer['title']}' "
                    f"(worth about ${offer['value_usd']}) — {top['reason']}. "
                    f"Would you like me to apply it?",
        "facts": {"offer": offer["title"], "value": f"${offer['value_usd']}",
                  "reason": top["reason"], "score": top["score"]},
        "offer_cards": [{"title": r["offer"]["title"], "value": r["offer"]["value_usd"],
                         "score": r["score"], "reason": r["reason"]} for r in remaining],
    }
