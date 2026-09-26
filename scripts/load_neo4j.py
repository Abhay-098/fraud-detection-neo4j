import argparse, os, hashlib
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
URI=os.getenv("NEO4J_URI","bolt://localhost:7687")
USER=os.getenv("NEO4J_USERNAME","neo4j")
PASSWORD=os.getenv("NEO4J_PASSWORD","password")
DB=os.getenv("NEO4J_DATABASE","neo4j")

SCHEMA=[
"CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE",
"CREATE CONSTRAINT account_id IF NOT EXISTS FOR (a:Account) REQUIRE a.account_id IS UNIQUE",
"CREATE CONSTRAINT transaction_id IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE",
"CREATE CONSTRAINT device_id IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE",
"CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.location_id IS UNIQUE",
"CREATE CONSTRAINT merchant_id IF NOT EXISTS FOR (m:Merchant) REQUIRE m.merchant_id IS UNIQUE",
"CREATE INDEX transaction_step IF NOT EXISTS FOR (t:Transaction) ON (t.step)",
"CREATE INDEX transaction_fraud IF NOT EXISTS FOR (t:Transaction) ON (t.is_fraud)",
]

def stable_num(value, mod):
    return int(hashlib.sha256(str(value).encode()).hexdigest()[:12],16)%mod

def make_row(r):
    origin=str(r.nameOrig); dest=str(r.nameDest)
    return {
        "transaction_id":str(r.transaction_id),"step":int(r.step),"type":str(r.type),
        "amount": float(r.amount),
        "origin": origin,
        "destination": dest,
        "is_fraud": bool(r.is_fraud),

        "oldbalanceOrg": float(r.oldbalanceOrg),
        "newbalanceOrig": float(r.newbalanceOrig),
        "oldbalanceDest": float(r.oldbalanceDest),
        "newbalanceDest": float(r.newbalanceDest),
        "device":"D"+f"{stable_num(origin,5000)+1:05d}",
        "location":"L"+f"{stable_num(str(origin)+str(int(r.step)),500)+1:04d}"
    }

def batch_tx(tx, rows):
    q="""
    UNWIND $rows AS row
    MERGE (oc:Customer {customer_id:row.origin})
    MERGE (oa:Account {account_id:'ACC_'+row.origin})
    MERGE (oc)-[:OWNS]->(oa)
    MERGE (od:Device {device_id:row.device})
    MERGE (oc)-[:USES]->(od)
    MERGE (oa)-[:ACCESSED_FROM]->(od)
    MERGE (ol:Location {location_id:row.location})
    CREATE (t:Transaction {
        transaction_id:row.transaction_id,
        step:row.step,
        type:row.type,
        amount:row.amount,
        origin:row.origin,
        destination:row.destination,
        oldbalanceOrg:row.oldbalanceOrg,
        newbalanceOrig:row.newbalanceOrig,
        oldbalanceDest:row.oldbalanceDest,
        newbalanceDest:row.newbalanceDest,
        is_fraud:row.is_fraud
    })
    CREATE (oa)-[:PERFORMS]->(t)
    FOREACH (_ IN CASE WHEN row.destination STARTS WITH 'M' THEN [1] ELSE [] END |
      MERGE (m:Merchant {merchant_id:row.destination})
      CREATE (t)-[:PAID_TO]->(m)
    )
    FOREACH (_ IN CASE WHEN NOT row.destination STARTS WITH 'M' THEN [1] ELSE [] END |
      MERGE (dc:Customer {customer_id:row.destination})
      MERGE (da:Account {account_id:'ACC_'+row.destination})
      MERGE (dc)-[:OWNS]->(da)
      CREATE (t)-[:SENT_TO]->(da)
    )
    CREATE (t)-[:OCCURRED_AT]->(ol)
    """
    tx.run(q,rows=rows).consume()

def main(path,batch=1000):
    df=pd.read_csv(path)
    driver=GraphDatabase.driver(URI,auth=(USER,PASSWORD))
    with driver.session(database=DB) as s:
        for q in SCHEMA: s.run(q).consume()
    with driver.session(database=DB) as s:
        for start in range(0,len(df),batch):
            rows=[make_row(r) for r in df.iloc[start:start+batch].itertuples()]
            s.execute_write(batch_tx,rows)
            print(f"Loaded {min(start+batch,len(df)):,}/{len(df):,}")
    driver.close()

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="data/processed/paysim_subset.csv")
    ap.add_argument("--batch",type=int,default=1000)
    args=ap.parse_args()
    main(args.input,args.batch)
