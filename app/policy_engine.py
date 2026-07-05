"""Deterministic policy engine (reference §policy engine, PoC scale). Reads the
current TurnFrame + state and emits a directive that shapes tone and can flag
escalation. Simple, explainable rules — no YAML file needed for the PoC."""
from dataclasses import dataclass


@dataclass
class Directive:
    tone: str = "clear"
    empathy: str = "normal"
    escalate: bool = False
    rule: str = "default"


def evaluate(frame, state):
    # Anger / strong negative -> de-escalate + flag
    if frame.sentiment == "NEG" and frame.sentiment_intensity >= 0.55:
        return Directive("de-escalating", "high", True, "irate_customer")
    # Sustained decline across turns -> empathetic + flag
    if state.sentiment_trend(3) == "declining":
        return Directive("empathetic", "high", True, "sentiment_declining")
    # Happy promo moment -> upbeat
    if frame.intent == "PROMO_INQUIRY" and frame.sentiment == "POS":
        return Directive("upbeat", "normal", False, "positive_promo")
    # Factual dispute -> investigative, must re-verify
    if frame.intent == "FACTUAL_DISPUTE":
        return Directive("apologetic-investigative", "high", False, "factual_dispute")
    return Directive()
