import os
import sys


# Add project root to Python path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from backend.database import session
from backend.fraud_detection import analyze_transaction


def get_test_transactions(limit=100):
    query = """
    MATCH (o:Account)-[:PERFORMS]->(t:Transaction)-[:SENT_TO]->(d:Account)
    WHERE coalesce(t.synthetic_demo, false) = false

    WITH o, t, d
    ORDER BY t.transaction_id

    WITH
        collect(
            CASE WHEN coalesce(t.is_fraud, false) = true
            THEN {
                id: t.transaction_id,
                origin: o.account_id,
                destination: d.account_id,
                amount: t.amount,
                type: t.type,
                actual: 1
            } END
        ) AS frauds,

        collect(
            CASE WHEN coalesce(t.is_fraud, false) = false
            THEN {
                id: t.transaction_id,
                origin: o.account_id,
                destination: d.account_id,
                amount: t.amount,
                type: t.type,
                actual: 0
            } END
        ) AS legitimate

    RETURN
        [x IN frauds WHERE x IS NOT NULL][0..$limit] +
        [x IN legitimate WHERE x IS NOT NULL][0..$limit]
        AS transactions
    """

    with session() as s:
        record = s.run(query, limit=limit).single()
        return record["transactions"]


def main():
    transactions = get_test_transactions(100)

    tp = 0
    tn = 0
    fp = 0
    fn = 0

    fraud_scores = []
    legitimate_scores = []

    for i, tx in enumerate(transactions, start=1):

        result = analyze_transaction(
            tx["origin"],
            tx["destination"],
            tx["amount"],
            tx["type"]
        )

        # Temporary evaluation threshold.
        # This does NOT change the application.
        predicted = 1 if result["risk_score"] >= 40 else 0
        actual = tx["actual"]

        if actual == 1:
            fraud_scores.append(result["risk_score"])
        else:
            legitimate_scores.append(result["risk_score"])

        if predicted == 1 and actual == 1:
            tp += 1
        elif predicted == 0 and actual == 0:
            tn += 1
        elif predicted == 1 and actual == 0:
            fp += 1
        else:
            fn += 1

        print(
            f"{i:3} | {tx['id']} | "
            f"Actual={actual} | "
            f"Score={result['risk_score']:3} | "
            f"Predicted={predicted}"
        )

    total = tp + tn + fp + fn

    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )

    print("\n========== RESULTS ==========")

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

    if fraud_scores:
        print(
            f"\nFraud scores      : "
            f"min={min(fraud_scores)}, "
            f"max={max(fraud_scores)}, "
            f"avg={sum(fraud_scores)/len(fraud_scores):.2f}"
        )

    if legitimate_scores:
        print(
            f"Legitimate scores : "
            f"min={min(legitimate_scores)}, "
            f"max={max(legitimate_scores)}, "
            f"avg={sum(legitimate_scores)/len(legitimate_scores):.2f}"
        )


if __name__ == "__main__":
    main()