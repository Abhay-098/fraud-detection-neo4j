import argparse, json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)

def main(inp):
    df=pd.read_csv(inp)
    out=Path("reports/figures"); out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"figure.figsize":(9,5),"axes.titlesize":14})
    plt.style.use("seaborn-v0_8-whitegrid")

    # 1 transaction types
    df["type"].value_counts().plot(kind="bar")
    plt.title("Transactions by Type"); plt.xlabel("Transaction type"); plt.ylabel("Count")
    plt.tight_layout(); plt.savefig(out/"01_transaction_types.png",dpi=180); plt.close()

    # 2 fraud composition
    labels=df["is_fraud"].map({0:"Legitimate",1:"Fraud"})
    labels.value_counts().plot(kind="bar")
    plt.title("Fraud vs Legitimate Transactions"); plt.ylabel("Count")
    plt.tight_layout(); plt.savefig(out/"02_fraud_vs_legitimate.png",dpi=180); plt.close()

    # 3 amount distribution
    plt.hist(df.sample(min(len(df),50000),random_state=42)["amount"],bins=50)
    plt.title("Transaction Amount Distribution"); plt.tight_layout()
    plt.savefig(out/"03_amount_distribution.png",dpi=180); plt.close()

    # 4 fraud rate by type
    rate=df.groupby("type")["is_fraud"].mean().sort_values(ascending=False)*100
    rate.plot(kind="bar")
    plt.title("Fraud Rate by Transaction Type"); plt.ylabel("Fraud rate (%)")
    plt.tight_layout(); plt.savefig(out/"04_fraud_rate_by_type.png",dpi=180); plt.close()

    # 5 transactions over time
    df.groupby("step").size().plot(kind="line")
    plt.title("Transactions Over Simulation Time"); plt.xlabel("Step"); plt.ylabel("Transactions")
    plt.tight_layout(); plt.savefig(out/"05_transaction_trend.png",dpi=180); plt.close()

    # 6 fraud over time
    df.groupby("step")["is_fraud"].sum().plot(kind="line")
    plt.title("Fraud Transactions Over Time"); plt.xlabel("Step"); plt.ylabel("Fraud transactions")
    plt.tight_layout(); plt.savefig(out/"06_fraud_trend.png",dpi=180); plt.close()

    # 7 amount vs fraud
    sample=df.sample(min(len(df),15000),random_state=42)
    plt.scatter(sample["amount"],sample["drain_ratio"],c=sample["is_fraud"],alpha=.45,s=12)
    plt.title("Amount vs Origin Drain Ratio"); plt.tight_layout()
    plt.savefig(out/"07_amount_vs_drain_ratio.png",dpi=180); plt.close()

    # 8 top origins
    top=df["nameOrig"].value_counts().head(15).sort_values()
    top.plot(kind="barh")
    plt.title("Top Originating Customers by Transaction Count"); plt.xlabel("Transactions")
    plt.tight_layout(); plt.savefig(out/"08_top_originators.png",dpi=180); plt.close()

    # 9 fraud amount
    df.boxplot(column="amount",by="is_fraud",showfliers=False,grid=False)
    plt.suptitle("")
    plt.title("Transaction Amount by Fraud Label"); plt.xlabel("Fraud label")
    plt.tight_layout(); plt.savefig(out/"09_amount_by_fraud.png",dpi=180); plt.close()

    # 10 confusion matrix for a simple transparent rule baseline
    threshold=float(df["amount"].quantile(.995))
    pred=((df["type"].isin(["TRANSFER","CASH-OUT"])) & (df["amount"]>=threshold)).astype(int)
    cm=confusion_matrix(df["is_fraud"],pred,labels=[0,1])
    plt.imshow(cm,interpolation="nearest")
    plt.colorbar()
    for (i,j),v in np.ndenumerate(cm): plt.text(j,i,str(v),ha="center",va="center")
    plt.xticks([0,1],["Pred. Legit","Pred. Fraud"]); plt.yticks([0,1],["Actual Legit","Actual Fraud"])
    plt.title("Confusion Matrix – Transparent Rule Baseline")
    plt.tight_layout(); plt.savefig(out/"10_confusion_matrix_rule.png",dpi=180); plt.close()

    metrics={
        "accuracy":float(accuracy_score(df["is_fraud"],pred)),
        "precision":float(precision_score(df["is_fraud"],pred,zero_division=0)),
        "recall":float(recall_score(df["is_fraud"],pred,zero_division=0)),
        "f1":float(f1_score(df["is_fraud"],pred,zero_division=0)),
        "roc_auc":float(roc_auc_score(df["is_fraud"],pred)) if df["is_fraud"].nunique()>1 else None,
        "pr_auc":float(average_precision_score(df["is_fraud"],pred)) if df["is_fraud"].nunique()>1 else None,
        "rule":"TRANSFER/CASH-OUT AND amount >= 99.5th percentile"
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    print(json.dumps(metrics,indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="data/processed/paysim_subset.csv")
    args=ap.parse_args(); main(args.input)
