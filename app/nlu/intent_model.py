"""M3 NLU — intent classifier. A TF-IDF vectorizer feeding an MLP (a small
neural network — sklearn's MLPClassifier) so this satisfies the 'deep-learning
based NLU' objective while staying dependency-light and CPU-fast for the PoC.

Falls back to a keyword classifier if the trained model isn't present, so the
app runs even before `python train_models.py` has been executed."""
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline

from .. import config
from . import dataset
from .preprocess import normalize

_MODEL_PATH = config.MODELS_DIR / "intent_mlp.joblib"
_model = None

# Minimal keyword backstop for the no-model case (keeps the demo alive).
_KEYWORDS = [
    ("HUMAN_HANDOFF", ["human", "agent", "manager", "supervisor", "real person"]),
    ("FACTUAL_DISPUTE", ["never", "didn't", "did not", "wasn't", "not me"]),
    ("HAGGLE", ["too expensive", "too much", "better deal", "cancel", "switching", "leaving"]),
    ("CREATE_TICKET", ["file a complaint", "formal dispute", "raise a ticket", "escalate"]),
    ("TICKET_STATUS", ["status", "update on my"]),
    ("BILL_DISPUTE", ["dispute", "wrong", "incorrect", "refund", "remove this"]),
    ("BILL_EXPLAIN", ["bill", "charge", "higher", "breakdown"]),
    ("PROMO_INQUIRY", ["offer", "deal", "discount", "promotion", "reward"]),
    ("PAYMENT_QUERY", ["payment", "paid", "pay"]),
    ("CONFIRM_YES", ["yes", "yeah", "sure", "ok", "accept", "go ahead"]),
    ("CONFIRM_NO", ["no ", "not interested", "pass", "nope"]),
    ("GREETING", ["hi", "hello", "hey"]),
    ("GOODBYE", ["bye", "goodbye", "that's all", "thank you bye"]),
]


def train_and_save():
    X = [normalize(t) for t, _ in dataset.INTENT_DATA]
    y = [lbl for _, lbl in dataset.INTENT_DATA]
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("mlp", MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1200,
                              alpha=0.01, random_state=42)),
    ])
    pipe.fit(X, y)
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, _MODEL_PATH)
    return pipe


def _load():
    global _model
    if _model is None and _MODEL_PATH.exists():
        _model = joblib.load(_MODEL_PATH)
    return _model


def _keyword_fallback(text):
    t = " " + normalize(text) + " "
    for intent, kws in _KEYWORDS:
        if any(k in t for k in kws):
            return intent, 0.40
    return "FALLBACK", 0.30


def classify(text):
    """Return (intent, confidence)."""
    model = _load()
    if model is None:
        return _keyword_fallback(text)
    norm = normalize(text)
    proba = model.predict_proba([norm])[0]
    classes = model.named_steps["mlp"].classes_
    idx = proba.argmax()
    intent, conf = classes[idx], float(proba[idx])
    # Low-confidence guard -> defer to keyword hints to avoid confident nonsense.
    if conf < 0.35:
        kw_intent, kw_conf = _keyword_fallback(text)
        if kw_intent != "FALLBACK":
            return kw_intent, max(conf, kw_conf)
    return intent, conf
