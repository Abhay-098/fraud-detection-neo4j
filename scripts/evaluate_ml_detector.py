import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from backend.database import session
from backend.ml_detection import predict_fraud


def get_transactions(limit=100):
    query = """
    MATCH (t:Transaction)
    WHERE coalesce(t.synthetic_demo, false) = false
      AND t.oldbalanceOrg IS NOT NULL
      AND t.newbalanceOrig IS NOT NULL
      AND t.oldbalanceDest IS NOT NULL
      AND t.newbalanceDest IS NOT NULL

    WITH t
    ORDER BY t.transaction_id

    WITH
        collect(CASE WHEN coalesce(t.is_fraud,false) = true THEN t END) AS frauds,
        collect(CASE WHEN coalesce(t.is_fraud,false) = false THEN t END) AS legitimate

    RETURN
        [t IN frauds WHERE t IS NOT NULL][0..$limit] +
        [t IN legitimate WHERE t IS NOT NULL][0..$limit]
        AS transactions
    """

    with session() as s:
        record = s.run(query, limit=limit).single()
        return [dict(t) for t in record["transactions"]]


def main():
    transactions = get_transactions(100)

    tp = tn = fp = fn = 0

    fraud_probabilities = []
    legitimate_probabilities = []

    for tx in transactions:

        result = predict_fraud(tx)

        predicted = result["prediction"]
        actual = 1 if tx.get("is_fraud", False) else 0
        probability = result["fraud_probability"]

        if actual == 1:
            fraud_probabilities.append(probability)
        else:
            legitimate_probabilities.append(probability)

        if predicted == 1 and actual == 1:
            tp += 1
        elif predicted == 0 and actual == 0:
            tn += 1
        elif predicted == 1 and actual == 0:
            fp += 1
        else:
            fn += 1

    total = tp + tn + fp + fn

    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    print("\n========== ML EVALUATION ==========")

    print(f"\nTransactions tested: {total}")

    print("\nConfusion Matrix")
    print(f"TP: {tp}")
    print(f"TN: {tn}")
    print(f"FP: {fp}")
    print(f"FN: {fn}")

    print("\nMetrics")
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")

    if fraud_probabilities:
        print(
            "\nFraud probabilities      : "
            f"min={min(fraud_probabilities):.4f}, "
            f"max={max(fraud_probabilities):.4f}, "
            f"avg={sum(fraud_probabilities)/len(fraud_probabilities):.4f}"
        )

    if legitimate_probabilities:
        print(
            "Legitimate probabilities : "
            f"min={min(legitimate_probabilities):.4f}, "
            f"max={max(legitimate_probabilities):.4f}, "
            f"avg={sum(legitimate_probabilities)/len(legitimate_probabilities):.4f}"
        )


def evaluate_thresholds():
    transactions = get_transactions(100)

    thresholds = [
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.35,
        0.40,
        0.45,
        0.50,
    ]

    print("\n========== THRESHOLD COMPARISON ==========")
    print("Threshold   TP   TN   FP   FN   Precision   Recall   F1")

    results = []

    predictions = []

    for tx in transactions:
        result = predict_fraud(tx)

        predictions.append({
            "actual": 1 if tx.get("is_fraud", False) else 0,
            "probability": result["fraud_probability"],
        })

    for threshold in thresholds:

        tp = tn = fp = fn = 0

        for item in predictions:

            predicted = (
                1
                if item["probability"] >= threshold
                else 0
            )

            actual = item["actual"]

            if predicted == 1 and actual == 1:
                tp += 1
            elif predicted == 0 and actual == 0:
                tn += 1
            elif predicted == 1 and actual == 0:
                fp += 1
            else:
                fn += 1

        precision = (
            tp / (tp + fp)
            if tp + fp
            else 0
        )

        recall = (
            tp / (tp + fn)
            if tp + fn
            else 0
        )

        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0
        )

        results.append(
            (threshold, tp, tn, fp, fn, precision, recall, f1)
        )

        print(
            f"{threshold:9.2f} "
            f"{tp:4} {tn:4} {fp:4} {fn:4} "
            f"{precision:11.4f} "
            f"{recall:8.4f} "
            f"{f1:8.4f}"
        )

    best = max(results, key=lambda x: x[7])

    print("\nBest F1 threshold on this evaluation sample:")
    print(f"Threshold: {best[0]:.2f}")
    print(f"Precision: {best[5]:.4f}")
    print(f"Recall   : {best[6]:.4f}")
    print(f"F1       : {best[7]:.4f}")


if __name__ == "__main__":
    main()
    evaluate_thresholds()