"""Hub-and-spoke COORDINATOR — the HUB.

The hub never answers directly. Each turn it:
  1. runs NLU  (text -> TurnFrame)
  2. asks the policy engine for a directive (tone / escalate)
  3. checks handoff triggers; may swap the active spoke  billing -> retention
  4. routes the turn to the active spoke's flow
  5. runs NLG to phrase the reply in the spoke persona's voice
  6. records the turn on shared ConversationState

Spokes:  billing spoke = persona 'Aria' (UC-01 billing + UC-02 offers)
         retention spoke = persona 'Ray' (specialist negotiation ladder)
The two spokes never call each other — only the hub moves control between them.
"""
import json
import time

from . import data_store, policy_engine
from .nlu import pipeline
from .nlg import generator
from .flows import billing_flow, offers_flow, retention_flow
from . import config

PERSONA = {"billing": "Aria", "retention": "Ray"}


# ── handoff triggers (billing spoke -> retention spoke) ───────────────────────
def _detect_handoff(frame, state, directive, flow_response):
    if state.active_spoke == "retention":
        return None
    if flow_response and flow_response.get("request_handoff"):
        return flow_response["request_handoff"]
    if frame.intent == "HUMAN_HANDOFF":
        return "customer_requested"
    if frame.intent == "HAGGLE":
        return "haggle"
    # only escalate on tone after at least 2 substantive turns
    if directive.escalate and len(state.turns) >= 2:
        return "negative_sentiment"
    return None


def _route_billing(state, frame):
    """Pick UC-01 vs UC-02 inside the billing spoke, honoring an active flow."""
    intent = frame.intent
    if intent == "TICKET_STATUS":
        return _ticket_status(state)
    if intent == "GREETING" and not state.active_flow:
        cust = data_store.get_customer(state.customer_id)
        return {"template": f"Hi {cust['first_name']}! I can explain your bill, help "
                "with a disputed charge, or check offers for you. What's on your mind?",
                "facts": {}}
    # continue an in-progress flow so confirmations route correctly
    if state.active_flow == "UC-02" or intent == "PROMO_INQUIRY":
        return offers_flow.handle(state, frame)
    if state.active_flow == "UC-01" or intent in (
            "BILL_EXPLAIN", "BILL_DISPUTE", "FACTUAL_DISPUTE", "CREATE_TICKET"):
        return billing_flow.handle(state, frame)
    # generic
    return {"template": "I can help with your bill, a disputed charge, or personalized "
            "offers. Which would you like?", "facts": {}}


def _ticket_status(state):
    tickets = data_store.list_tickets(state.customer_id)
    if not tickets:
        return {"template": "You don't have any open dispute tickets right now.", "facts": {}}
    t = tickets[-1]
    return {"template": f"Your ticket {t['ticket_id']} ({t['subject']}) is currently "
            f"{t['status']} with a {t['sla_hours']}h SLA.",
            "facts": {"ticket": t["ticket_id"], "status": t["status"]}}


def handle_turn(state, text, use_llm=True):
    t0 = time.time()
    frame = pipeline.understand(text)
    directive = policy_engine.evaluate(frame, state)

    handoff_now = False
    if state.active_spoke == "billing":
        flow_response = _route_billing(state, frame)
        reason = _detect_handoff(frame, state, directive, flow_response)
        if reason:
            handoff_now = True
            _do_handoff(state, reason)
            flow_response = _retention_intro(state, frame)
    else:
        flow_response = retention_flow.handle(state, frame)

    persona = PERSONA[state.active_spoke]
    text_out = generator.compose(persona, flow_response["template"],
                                 facts=flow_response.get("facts"),
                                 directive=directive, use_llm=use_llm)

    response = {
        "speaker": persona,
        "text": text_out,
        "template": flow_response["template"],
        "spoke": state.active_spoke,
        "intent": frame.intent,
        "intent_conf": frame.intent_conf,
        "sentiment": frame.sentiment,
        "sentiment_score": frame.sentiment_score,
        "directive": directive.rule,
        "escalate": directive.escalate,
        "handoff": handoff_now,
        "handoff_reason": state.handoff_reason,
        "offer_cards": flow_response.get("offer_cards"),
        "action": state.actions[-1] if state.actions else None,
        "resolution_status": state.resolution_status,
    }
    latency = round((time.time() - t0) * 1000)
    response["latency_ms"] = latency
    state.record(frame, response, latency_ms=latency)
    return response


def _do_handoff(state, reason):
    state.active_spoke = "retention"
    state.handoff_reason = reason
    state.flow_step = "retention_intro"
    state.slots["retention_rung"] = 0
    state.escalation_flags.append(f"handoff:{reason}")


def _retention_intro(state, frame):
    """Bridge line + specialist opening + first ladder pitch, as one turn."""
    opening = retention_flow.opening_line(state.handoff_reason)
    pitch = retention_flow.handle(state, frame)
    pitch["template"] = f"{opening} {pitch['template']}"
    return pitch


def start_session(customer_id):
    from .conversation_state import ConversationState
    sid = f"sess_{customer_id}_{int(time.time())}"
    return ConversationState(session_id=sid, customer_id=customer_id)


def save_session(state):
    path = config.SESSIONS_DIR / f"{state.session_id}.json"
    log = state.as_log()
    log["resolution_status"] = state.resolution_status
    path.write_text(json.dumps(log, indent=2))
    return path
