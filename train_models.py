"""M3 — train + save the NLU models, then print a quick evaluation.
Run once before launching the app:   python train_models.py"""
from app.nlu import intent_model, sentiment_model
from app.metrics import evaluate_intent_model, evaluate_sentiment_model


def main():
    print("Training intent MLP ...")
    intent_model.train_and_save()
    print("Training sentiment MLP ...")
    sentiment_model.train_and_save()
    print("\n=== NLU evaluation (held-out split) ===")
    evaluate_intent_model(verbose=True)
    evaluate_sentiment_model(verbose=True)
    print("\nModels saved to app/nlu/models/. You can now run the app.")


if __name__ == "__main__":
    main()
