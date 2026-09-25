import argparse
import json
from pathlib import Path

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
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

TARGET = "is_fraud"


def evaluate_model(model, X_test, y_test):
    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]

    return {
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, prob),
        "pr_auc": average_precision_score(y_test, prob),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
    }


def main(inp):
    df = pd.read_csv(inp)

    X = df[FEATURES].copy()
    y = df[TARGET].astype(int)

    cat = ["type"]
    num = [c for c in FEATURES if c not in cat]

    preprocessor = ColumnTransformer(
        [
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                cat,
            ),
            (
                "num",
                StandardScaler(),
                num,
            ),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        stratify=y,
        random_state=42,
    )

    class_weights = [
        None,
        "balanced",
        {0: 1, 1: 5},
        {0: 1, 1: 10},
        {0: 1, 1: 20},
        {0: 1, 1: 30},
        {0: 1, 1: 50},
        {0: 1, 1: 75},
        {0: 1, 1: 100},
    ]

    experiments = []

    for weight in class_weights:

        model = Pipeline(
            [
                ("pre", preprocessor),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight=weight,
                        solver="liblinear",
                    ),
                ),
            ]
        )

        model.fit(X_train, y_train)

        metrics = evaluate_model(
            model,
            X_test,
            y_test,
        )

        metrics["class_weight"] = weight
        experiments.append(metrics)

    best = max(
        experiments,
        key=lambda x: x["f1"]
    )

    output = {
        "dataset": inp,
        "test_size": 0.25,
        "random_state": 42,
        "selection_metric": "f1",
        "number_of_experiments": len(experiments),
        "best_model": best,
        "all_experiments": experiments,
        "features": FEATURES,
    }

    Path("reports").mkdir(exist_ok=True)

    Path("reports/baseline_metrics.json").write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default="data/processed/paysim_subset.csv"
    )

    args = parser.parse_args()

    main(args.input)