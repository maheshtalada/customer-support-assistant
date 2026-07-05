"""M3 NLU — entity extraction. Rule/regex based (standard for slot-filling in a
PoC NLU pipeline). Pulls the structured slots the flows need: which charge the
customer means, money amounts, offer ids, yes/no, and the dispute topic."""
import re
from .preprocess import normalize

_CHARGE_ID = re.compile(r"\bCHG-[A-Z0-9\-]+\b", re.I)
_OFFER_ID = re.compile(r"\bOFFER-[A-Z0-9\-]+\b", re.I)
_AMOUNT = re.compile(r"\$?\s?(\d+(?:\.\d+)?)\s?(?:dollars|usd|rs|rupees)?", re.I)

_TOPIC_KEYWORDS = {
    "ROAMING": ["roaming", "mexico", "abroad", "international", "travel"],
    "OVERAGE": ["overage", "data", "cap", "gb", "over my limit", "extra data"],
    "TAX": ["tax", "fees", "surcharge"],
    "PLAN": ["plan charge", "base plan", "monthly plan"],
}


def extract(text):
    raw = text or ""
    norm = normalize(raw)
    ent = {
        "charge_ids": _CHARGE_ID.findall(raw),
        "offer_ids": _OFFER_ID.findall(raw),
        "dispute_topic": None,
        "affirmation": None,
    }

    for topic, kws in _TOPIC_KEYWORDS.items():
        if any(k in norm for k in kws):
            ent["dispute_topic"] = topic
            break

    if re.search(r"\b(yes|yeah|yep|sure|ok|okay|accept|go ahead|please do)\b", norm):
        ent["affirmation"] = True
    elif re.search(r"\b(no|nope|nah|not interested|pass|don't)\b", norm):
        ent["affirmation"] = False

    return ent
