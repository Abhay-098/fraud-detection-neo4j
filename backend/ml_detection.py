from pathlib import Path

import joblib
import pandas as pd


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "fraud_model.joblib"
)

FEATURES = [
    "step",
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
]


_model = None


def get_model():
    global _model

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Fraud model not found: {MODEL_PATH}"
            )

        _model = joblib.load(MODEL_PATH)

    return _model


def predict_fraud(transaction):
    model = get_model()

    row = {
        "step": int(transaction["step"]),
        "type": str(transaction["type"]),
        "amount": float(transaction["amount"]),
        "oldbalanceOrg": float(transaction["oldbalanceOrg"]),
        "newbalanceOrig": float(transaction["newbalanceOrig"]),
        "oldbalanceDest": float(transaction["oldbalanceDest"]),
        "newbalanceDest": float(transaction["newbalanceDest"]),
    }

    X = pd.DataFrame([row], columns=FEATURES)

    probability = float(
        model.predict_proba(X)[0][1]
    )

    THRESHOLD = 0.10

    prediction = int(
        probability >= THRESHOLD
    )

    return {
        "prediction": prediction,
        "label": "FRAUD" if prediction == 1 else "LEGITIMATE",
        "fraud_probability": round(probability, 6),
        "fraud_probability_percent": round(probability * 100, 2),
        "threshold": THRESHOLD,
        "model": "Logistic Regression",
    }