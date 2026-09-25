import argparse
from pathlib import Path
import pandas as pd
import numpy as np

REQUIRED=["step","type","amount","nameOrig","oldbalanceOrg","newbalanceOrig",
          "nameDest","oldbalanceDest","newbalanceDest","isFraud","isFlaggedFraud"]

def prepare(inp,out,rows=None,demo=False):
    df=pd.read_csv(inp)
    missing=[c for c in REQUIRED if c not in df.columns]
    if missing: raise ValueError(f"Missing columns: {missing}")
    if rows:
        df=df.sort_values("step").head(rows)
    df["transaction_id"]=[f"TX{idx:09d}" for idx in range(1,len(df)+1)]
    df["origin_external"]=df["nameOrig"].astype(str).str.startswith("M")
    df["destination_external"]=df["nameDest"].astype(str).str.startswith("M")
    df["drain_ratio"]=(df["amount"]/(df["oldbalanceOrg"]+1)).clip(0,10)
    df["balance_error_orig"]=np.abs(df["oldbalanceOrg"]-df["amount"]-df["newbalanceOrig"])
    df["balance_error_dest"]=np.abs(df["oldbalanceDest"]+df["amount"]-df["newbalanceDest"])
    df["amount_log"]=np.log1p(df["amount"])
    df["is_fraud"]=df["isFraud"].astype(int)
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(out,index=False)
    print(f"Prepared {len(df):,} rows -> {out}")
    print("Fraud:", int(df["is_fraud"].sum()), "Non-fraud:", int((1-df["is_fraud"]).sum()))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",default="data/processed/paysim_subset.csv")
    ap.add_argument("--rows",type=int,default=250000)
    ap.add_argument("--demo",action="store_true")
    args=ap.parse_args()
    prepare(args.input,args.output,args.rows,args.demo)
