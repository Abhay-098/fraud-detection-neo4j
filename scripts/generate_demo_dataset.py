import argparse
from pathlib import Path
import numpy as np
import pandas as pd

def make_demo(rows=25000, seed=42):
    rng=np.random.default_rng(seed)
    steps=rng.integers(1,745,size=rows)
    types=rng.choice(["CASH-IN","CASH-OUT","DEBIT","PAYMENT","TRANSFER"],size=rows,p=[.15,.25,.03,.42,.15])
    amount=np.round(rng.lognormal(mean=8.0,sigma=1.0,size=rows),2)
    orig=rng.integers(1,8000,size=rows)
    dest=rng.integers(1,9000,size=rows)
    nameOrig=np.array([f"C{v:08d}" for v in orig])
    nameDest=np.array([("M" if rng.random()<.22 else "C")+f"{v:08d}" for v in dest])
    old=np.round(rng.lognormal(mean=9.0,sigma=1.1,size=rows),2)
    new=np.maximum(0,np.round(old-amount,2))
    oldd=np.round(rng.lognormal(mean=9.0,sigma=1.1,size=rows),2)
    newd=np.round(oldd+amount,2)
    fraud=np.zeros(rows,dtype=int)
    candidate=(np.isin(types,["TRANSFER","CASH-OUT"]) & (amount>np.quantile(amount,.985)))
    idx=np.where(candidate)[0]
    fraud[idx[:max(20,int(rows*.002))]]=1
    flagged=((types=="TRANSFER")&(amount>200000)).astype(int)
    return pd.DataFrame({
        "step":steps,"type":types,"amount":amount,"nameOrig":nameOrig,
        "oldbalanceOrg":old,"newbalanceOrig":new,"nameDest":nameDest,
        "oldbalanceDest":oldd,"newbalanceDest":newd,
        "isFraud":fraud,"isFlaggedFraud":flagged
    }).sort_values("step").reset_index(drop=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--rows",type=int,default=25000)
    ap.add_argument("--output",default="data/demo/paysim_demo.csv")
    args=ap.parse_args()
    p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True)
    make_demo(args.rows).to_csv(p,index=False)
    print(f"Wrote {len(make_demo(args.rows)):,} demo rows to {p}")
