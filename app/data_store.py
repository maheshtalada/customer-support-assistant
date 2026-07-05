"""M1 Data Collection — loads the synthetic telco data and exposes simple
accessors used by the whole chatbot. Tickets are read/written back to disk so
dispute tickets created during a chat persist. PoC-simple, no DB."""
import json
from . import config

_TELCO = json.loads((config.DATA_DIR / "synthetic_telco.json").read_text())
_TICKETS_PATH = config.DATA_DIR / "synthetic_tickets.json"


def _load_tickets():
    return json.loads(_TICKETS_PATH.read_text())


# ── Customer / account lookups ───────────────────────────────────────────────
def all_customers():
    return _TELCO["customers"]


def get_customer(cid):
    return _TELCO["customers"].get(cid)


def find_customer_by_email(email):
    for cid, c in _TELCO["customers"].items():
        if c["email"].lower() == (email or "").lower():
            return c
    return None


def get_bill(cid):
    return _TELCO["bills"].get(cid)


def get_payments(cid):
    return _TELCO["payments"].get(cid, [])


def get_usage(cid):
    return _TELCO["usage_history"].get(cid, [])


def get_interactions(cid):
    return _TELCO["interaction_history"].get(cid, [])


def get_plan(plan_id):
    return _TELCO["plans"].get(plan_id)


def all_offers():
    return _TELCO["promotions"]["OFFERS"]


def get_offer(offer_id):
    return next((o for o in all_offers() if o["offer_id"] == offer_id), None)


def dispute_policy():
    return _TELCO["dispute_policies"]


def disputable_charges(cid):
    """Line items a customer is likely to dispute (roaming/overage with evidence)."""
    bill = get_bill(cid) or {}
    return [li for li in bill.get("line_items", [])
            if li.get("type") in ("ROAMING", "OVERAGE")]


# ── Tickets (persisted) ──────────────────────────────────────────────────────
def list_tickets(cid=None):
    tickets = _load_tickets()["tickets"]
    return [t for t in tickets if cid is None or t["customer_id"] == cid]


def create_dispute_ticket(cid, charge_id, reason, session_id=None):
    import time, uuid
    data = _load_tickets()
    tkt = {
        "ticket_id": f"TKT-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": cid,
        "subject": f"Billing dispute for charge {charge_id}",
        "reason": reason,
        "status": "OPEN",
        "category": "BILLING_DISPUTE",
        "charge_id": charge_id,
        "session_id": session_id,
        "sla_hours": 48,
        "created_ts": time.time(),
        "updated_ts": time.time(),
        "history": [{"event": "created", "status": "OPEN", "by": "billing-agent"}],
    }
    data["tickets"].append(tkt)
    _TICKETS_PATH.write_text(json.dumps(data, indent=2))
    return tkt
