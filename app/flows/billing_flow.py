"""UC-01 Billing / Payment Dispute Resolution flow (front-line 'billing' spoke).

State machine:
  idle -> explain bill + surface the unusual charge
       -> (factual dispute) present evidence
       -> present resolution options (provisional credit if tier-eligible,
          or open a formal dispute ticket)
       -> apply chosen resolution (credit / ticket / waiver)
Returns a response dict; mutates ConversationState."""
from .. import data_store


def _primary_charge(cid):
    charges = data_store.disputable_charges(cid)
    return charges[0] if charges else None


def _fmt_evidence(charge):
    ev = charge.get("evidence", {})
    if charge["type"] == "ROAMING":
        return (f"our network logs show a roaming session on towers "
                f"{', '.join(ev.get('tower_ids', []))} during {ev.get('dates')}")
    if charge["type"] == "OVERAGE":
        return (f"metering shows {ev.get('usage_gb')} GB used in the window "
                f"{ev.get('window')}, beyond your plan cap")
    return "the usage records on file"


def handle(state, frame):
    cid = state.customer_id
    cust = data_store.get_customer(cid)
    bill = data_store.get_bill(cid)
    charge = _primary_charge(cid)
    state.active_flow = "UC-01"

    # ── step: explain the bill + surface the odd charge ──────────────────────
    if state.flow_step in ("idle", "") or frame.intent in ("BILL_EXPLAIN", "BILL_DISPUTE"):
        if state.flow_step in ("idle", ""):
            state.flow_step = "await_validate"
            state.resolution_status = "in_progress"
            if charge:
                state.slots["charge_id"] = charge["charge_id"]
                delta = bill["total_usd"] - bill["previous_usd"]
                tmpl = (f"Your {bill['cycle']} bill is ${bill['total_usd']}, up "
                        f"${delta} from last month. The difference is a "
                        f"${charge['amount_usd']} {charge['description']}. "
                        f"Does that charge look right to you?")
                return {"template": tmpl, "facts": {
                    "total": f"${bill['total_usd']}", "delta": f"${delta}",
                    "charge": charge["description"],
                    "amount": f"${charge['amount_usd']}"}}
            return {"template": f"Your {bill['cycle']} bill is ${bill['total_usd']} "
                    "and everything looks standard — plan charge plus taxes. "
                    "Is there a specific line item you'd like me to check?",
                    "facts": {"total": f"${bill['total_usd']}"}}

    # ── step: customer disputes -> present evidence + resolution options ──────
    if frame.intent in ("FACTUAL_DISPUTE", "BILL_DISPUTE") or state.flow_step == "await_validate":
        if charge:
            state.flow_step = "await_resolution_choice"
            state.slots["charge_id"] = charge["charge_id"]
            options = _resolution_options(cust, charge)
            tmpl = (f"I understand. I re-checked and {_fmt_evidence(charge)}. "
                    f"Here's what I can do: {options['sentence']}")
            return {"template": tmpl,
                    "facts": {"charge": charge["description"], **options["facts"]},
                    "resolution_options": options["kinds"]}

    # ── step: apply the chosen resolution ────────────────────────────────────
    if state.flow_step == "await_resolution_choice":
        return _apply_resolution(state, frame, cust, charge)

    # generic fallback within billing
    return {"template": "I can pull up your bill, explain any charge, or open a "
            "dispute for you. What would you like to do?", "facts": {}}


def _resolution_options(cust, charge):
    """Which resolutions are available, given tier + charge type."""
    tier = cust["loyalty_tier"]
    pol = data_store.dispute_policy()["provisional_credit"]["eligibility_by_tier"][tier]
    kinds, facts = [], {}
    if pol["eligible"]:
        kinds.append("credit")
        facts["provisional_credit"] = f"up to ${pol['max_usd']}"
        credit_txt = (f"apply a provisional credit of ${min(charge['amount_usd'], pol['max_usd'])} "
                      f"right now while we investigate (48h SLA)")
    elif charge["type"] == "OVERAGE":
        # Bronze overage -> the one-time 50% waiver offer instead of a credit.
        kinds.append("waiver")
        credit_txt = ("apply a one-time 50% goodwill waiver on the overage "
                      f"(${round(charge['amount_usd'] * 0.5)} off)")
        facts["waiver"] = f"${round(charge['amount_usd'] * 0.5)}"
    else:
        credit_txt = "escalate this to a specialist who can authorize a credit"
    kinds.append("ticket")
    sentence = f"I can {credit_txt}, or open a formal dispute ticket. Which would you prefer?"
    return {"sentence": sentence, "facts": facts, "kinds": kinds}


def _apply_resolution(state, frame, cust, charge):
    text = frame.text.lower()
    cid = state.customer_id
    wants_ticket = frame.intent == "CREATE_TICKET" or any(
        w in text for w in ["ticket", "formal", "dispute", "complaint", "escalate"])
    wants_credit = frame.intent == "CONFIRM_YES" or frame.entities.get("affirmation") or any(
        w in text for w in ["credit", "waiver", "waive", "refund", "yes"])

    if wants_ticket and not wants_credit:
        tkt = data_store.create_dispute_ticket(
            cid, charge["charge_id"], frame.text, state.session_id)
        state.actions.append({"type": "ticketing.create_dispute",
                              "status": "SUCCESS", "ticket_id": tkt["ticket_id"]})
        state.resolution_status = "resolved"
        state.flow_step = "resolved"
        return {"template": f"Done — I've opened dispute ticket {tkt['ticket_id']} "
                f"for the {charge['description']}. You'll get an update within 48 hours.",
                "facts": {"ticket_id": tkt["ticket_id"], "sla": "48 hours"}}

    if wants_credit:
        tier = cust["loyalty_tier"]
        pol = data_store.dispute_policy()["provisional_credit"]["eligibility_by_tier"][tier]
        if pol["eligible"]:
            amt = min(charge["amount_usd"], pol["max_usd"])
            kind = "provisional credit"
        elif charge["type"] == "OVERAGE":
            amt = round(charge["amount_usd"] * 0.5)
            kind = "50% goodwill waiver"
        else:
            state.flow_step = "await_resolution_choice"
            return {"template": "That credit needs specialist sign-off — let me bring "
                    "in our retention specialist.", "facts": {}, "request_handoff": "voice_cannot_resolve"}
        state.actions.append({"type": "billing.apply_credit", "status": "SUCCESS",
                              "amount_usd": amt, "kind": kind})
        state.resolution_status = "resolved"
        state.flow_step = "resolved"
        return {"template": f"All set — I've applied a ${amt} {kind} to your account "
                f"for the {charge['description']}. Your bill will reflect it shortly.",
                "facts": {"credit": f"${amt}", "kind": kind}}

    return {"template": "Would you like the credit now, or should I open a formal "
            "dispute ticket instead?", "facts": {}}
