"""M3 NLU — sentiment analysis. Same TF-IDF + MLP recipe, 3 classes
(POS/NEU/NEG). Returns a label plus a signed score in [-1, 1] and an intensity,
which the policy engine uses to detect declining sentiment / anger.

Lexical fallback keeps a signed score when no trained model is present."""
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline

from .. import config
from . import dataset
from .preprocess import normalize

_MODEL_PATH = config.MODELS_DIR / "sentiment_mlp.joblib"
_model = None

_POS_WORDS = {"thanks", "thank", "great", "perfect", "awesome", "love", "good",
              "happy", "wonderful", "excellent", "appreciate", "nice"}
_NEG_WORDS = {"ridiculous", "frustrated", "unacceptable", "angry", "worst",
              "scam", "terrible", "wrong", "unfair", "hate", "fed", "annoyed",
              "furious", "disappointed", "cancel"}
_SCORE = {"POS": 0.6, "NEU": 0.0, "NEG": -0.6}


def train_and_save():
    X = [normalize(t) for t, _ in dataset.SENTIMENT_DATA]
    y = [lbl for _, lbl in dataset.SENTIMENT_DATA]
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("mlp", MLPClassifier(hidden_layer_sizes=(32,), max_iter=1200,
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


def _lexical(text):
    toks = set(normalize(text).split())
    pos, neg = len(toks & _POS_WORDS), len(toks & _NEG_WORDS)
    if pos == neg == 0:
        return "NEU", 0.0, 0.0
    label = "POS" if pos > neg else "NEG" if neg > pos else "NEU"
    score = (pos - neg) / max(pos + neg, 1) * 0.7
    return label, round(score, 2), abs(score)


def analyze(text):
    """Return (label, score in [-1,1], intensity in [0,1])."""
    model = _load()
    if model is None:
        return _lexical(text)
    proba = model.predict_proba([normalize(text)])[0]
    classes = list(model.named_steps["mlp"].classes_)
    label = classes[proba.argmax()]
    # Expected signed score from class probabilities -> smooth trajectory.
    score = sum(_SCORE[c] * p for c, p in zip(classes, proba))
    return label, round(float(score), 2), round(float(max(proba)), 2)
