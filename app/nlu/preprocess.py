"""M2 Data Preparation — text cleaning/normalization shared by training and
runtime so the model always sees text the same way. PoC-simple."""
import re

_CONTRACTIONS = {
    "won't": "will not", "can't": "cannot", "n't": " not", "'m": " am",
    "'re": " are", "'ll": " will", "'ve": " have", "'d": " would",
}


def normalize(text: str) -> str:
    t = (text or "").lower().strip()
    for k, v in _CONTRACTIONS.items():
        t = t.replace(k, v)
    t = re.sub(r"[^a-z0-9$%\s]", " ", t)   # keep $ and % — meaningful for billing
    t = re.sub(r"\s+", " ", t).strip()
    return t
