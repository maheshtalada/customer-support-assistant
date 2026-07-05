"""M6 — print the objective-#5 evaluation: NLU model metrics + live KPIs.
Run:  python evaluate.py"""
from app import metrics


def main():
    print("=== NLU model evaluation (held-out split) ===")
    metrics.evaluate_intent_model(verbose=True)
    metrics.evaluate_sentiment_model(verbose=True)
    print("\n=== Live conversation KPIs (from data/sessions/*.json) ===")
    for k, v in metrics.conversation_metrics().items():
        print(f"  {k:18}: {v}")


if __name__ == "__main__":
    main()
