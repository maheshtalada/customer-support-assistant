"""Deterministic offer recommendation engine (reference §recommendation engine,
PoC scale). Customer signals -> LOW/MED/HIGH bands -> per-offer eligibility +
weighted score -> ranked Top-N. The RL bandit (M5) then re-weights the ranking
using learned accept/decline feedback.

Uses the 4 offers actually present in synthetic_telco.json, mapped to the 3
synthetic customers, so it is fully self-contained and runnable."""
from . import data_store
from .rl import bandit


# ── band helpers ─────────────────────────────────────────────────────────────
def _churn_band(cust):
    """Cheap churn proxy from interactions + escalations (no Neo4j in PoC)."""
    ixns = data_store.get_interactions(cust["customer_id"])
    escalated = any(i.get("outcome") == "ESCALATED" for i in ixns)
    if escalated or len(ixns) >= 2:
        return "HIGH"
    return "MEDIUM" if ixns else "LOW"


def _tenure_band(m):
    return "HIGH" if m >= 36 else "MEDIUM" if m >= 7 else "LOW"


def _usage_band(cust):
    usage = data_store.get_usage(cust["customer_id"])
    if not usage:
        return "LOW"
    latest = usage[0]
    if "data_gb_used" in latest and latest.get("data_cap_gb"):
        pct = latest["data_gb_used"] / latest["data_cap_gb"]
        return "HIGH" if pct >= 0.9 else "MEDIUM" if pct >= 0.6 else "LOW"
    return "LOW"


def customer_params(cust):
    return {
        "tier": cust["loyalty_tier"],
        "tenure_months": cust["tenure_months"],
        "tenure_band": _tenure_band(cust["tenure_months"]),
        "churn_band": _churn_band(cust),
        "usage_band": _usage_band(cust),
        "has_overage": any(li["type"] == "OVERAGE"
                           for li in (data_store.get_bill(cust["customer_id"]) or {}).get("line_items", [])),
    }


# ── eligibility + scoring ────────────────────────────────────────────────────
def _eligible(offer, cust, params):
    if cust["tenure_months"] < offer.get("min_tenure_months", 0):
        return False
    target = offer.get("target_tier", "ANY")
    if target not in ("ANY", cust["loyalty_tier"]):
        return False
    # Bronze overage waiver only makes sense if there IS an overage charge.
    if offer["offer_id"] == "OFFER-RETENTION-BRONZE-WAIVER" and not params["has_overage"]:
        return False
    return True


def _base_score(offer, cust, params):
    """Weighted heuristic score in ~[0,1] — higher churn/usage/tenure => higher."""
    band = {"LOW": 0.2, "MEDIUM": 0.55, "HIGH": 0.9}
    s = 0.35
    s += 0.30 * band[params["churn_band"]]
    if offer.get("applies_to") == "DATA_ADDON":
        s += 0.25 * band[params["usage_band"]]
    if offer.get("target_tier") == cust["loyalty_tier"]:
        s += 0.15
    if params["has_overage"] and "WAIVER" in offer["offer_id"]:
        s += 0.20
    return min(round(s, 3), 1.0)


def recommend(cust, top_n=3, use_rl=True):
    params = customer_params(cust)
    scored = []
    for offer in data_store.all_offers():
        if not _eligible(offer, cust, params):
            continue
        base = _base_score(offer, cust, params)
        final = bandit.adjust_score(offer["offer_id"], base) if use_rl else base
        scored.append({
            "offer": offer,
            "base_score": base,
            "score": round(final, 3),
            "reason": _reason(offer, cust, params),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n], params


def _reason(offer, cust, params):
    oid = offer["offer_id"]
    if "LOYALTY" in oid:
        return f"{cust['tenure_months']}-month {cust['loyalty_tier']} loyalty reward"
    if "DATA" in oid:
        return f"data usage is {params['usage_band']} — extra data avoids overage"
    if "FAMILY" in oid:
        return "eligible to consolidate onto a family plan"
    if "WAIVER" in oid:
        return "one-time goodwill waiver on the current overage charge"
    return "matched to your account profile"
