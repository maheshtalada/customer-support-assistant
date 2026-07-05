"""Shared per-session state — the single object the hub and both spokes read
and write. Mirrors the reference 'ConversationState' at PoC scale."""
import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ConversationState:
    session_id: str
    customer_id: str
    # hub-and-spoke routing
    active_spoke: str = "billing"          # "billing" | "retention"
    handoff_reason: Optional[str] = None
    # active flow within the current spoke
    active_flow: str = ""                  # "UC-01" | "UC-02" | ""
    flow_step: str = "idle"
    slots: dict = field(default_factory=dict)
    # trajectories / history
    turns: List[dict] = field(default_factory=list)
    intent_history: List[str] = field(default_factory=list)
    sentiment_trajectory: List[float] = field(default_factory=list)
    # offers
    offers_pitched: List[str] = field(default_factory=list)
    offers_declined: List[str] = field(default_factory=list)
    offer_accepted: Optional[str] = None
    # outcome
    actions: List[dict] = field(default_factory=list)
    escalation_flags: List[str] = field(default_factory=list)
    resolution_status: str = "open"        # open|in_progress|resolved|escalated

    def record(self, frame, response, latency_ms=0):
        self.intent_history.append(frame.intent)
        self.sentiment_trajectory.append(frame.sentiment_score)
        self.turns.append({
            "ts": time.time(),
            "user": frame.text,
            "intent": frame.intent,
            "intent_conf": frame.intent_conf,
            "sentiment": frame.sentiment,
            "sentiment_score": frame.sentiment_score,
            "spoke": self.active_spoke,
            "agent": response.get("speaker"),
            "reply": response.get("text"),
            "latency_ms": latency_ms,
            "feedback": None,
        })

    def sentiment_trend(self, n=3):
        """'declining' if the last n scores are strictly falling and negative."""
        arc = self.sentiment_trajectory[-n:]
        if len(arc) < n:
            return "stable"
        if all(arc[i] > arc[i + 1] for i in range(len(arc) - 1)) and arc[-1] < 0:
            return "declining"
        return "stable"

    def as_log(self):
        return {
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "active_flow": self.active_flow,
            "resolution_status": self.resolution_status,
            "handoff_reason": self.handoff_reason,
            "intent_path": self.intent_history,
            "sentiment_trajectory": self.sentiment_trajectory,
            "offers_pitched": self.offers_pitched,
            "offer_accepted": self.offer_accepted,
            "actions": self.actions,
            "escalation_flags": self.escalation_flags,
            "turns": self.turns,
        }
