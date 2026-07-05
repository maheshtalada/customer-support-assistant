"""M6 Monitoring/Evaluation — objective #5 metrics.
  - NLU model quality: accuracy / precision / recall / F1 on a held-out split
  - Live conversation metrics: resolution rate, avg latency, from session logs"""
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline

from . import config
from .nlu import dataset
from .nlu.preprocess import normalize


def _eval(data, hidden, title, verbose):
    X = [normalize(t) for t, _ in data]
    y = [lbl for _, lbl in data]
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.25, random_state=7, stratify=y)
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("mlp", MLPClassifier(hidden_layer_sizes=hidden, max_iter=800,
                              random_state=42)),
    ]).fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    acc = accuracy_score(yte, pred)
    report = classification_report(yte, pred, zero_division=0)
    if verbose:
        print(f"\n[{title}]  accuracy={acc:.2%}")
        print(report)
    return {"accuracy": acc, "report": report}


def evaluate_intent_model(verbose=False):
    return _eval(dataset.INTENT_DATA, (64, 32), "Intent MLP", verbose)


def evaluate_sentiment_model(verbose=False):
    return _eval(dataset.SENTIMENT_DATA, (32,), "Sentiment MLP", verbose)


def conversation_metrics():
    """Aggregate live KPIs from persisted session logs (objective #5)."""
    sessions, resolved, latencies, feedback = 0, 0, [], []
    for f in config.SESSIONS_DIR.glob("*.json"):
        try:
            s = json.loads(f.read_text())
        except Exception:
            continue
        sessions += 1
        if s.get("resolution_status") in ("resolved", "escalated"):
            resolved += 1
        latencies += [t.get("latency_ms", 0) for t in s.get("turns", [])
                      if t.get("latency_ms")]
        feedback += [t["feedback"] for t in s.get("turns", []) if t.get("feedback")]
    up = sum(1 for f in feedback if f == "up")
    return {
        "sessions": sessions,
        "resolution_rate": round(resolved / sessions, 2) if sessions else 0.0,
        "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else 0,
        "csat_proxy": round(up / len(feedback), 2) if feedback else None,
        "feedback_count": len(feedback),
    }
