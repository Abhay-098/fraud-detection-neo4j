from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .database import verify_connection
from .crud import list_transactions, create_transaction, update_transaction, delete_transaction
from .fraud_detection import shared_devices, cycles, high_risk_accounts, rings, summary

app = FastAPI(title="Neo4j Fraud Detection API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TransactionIn(BaseModel):
    transaction_id: str
    step: int
    type: str
    amount: float
    origin: str
    destination: str
    is_fraud: bool = False

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[str] = None
    is_fraud: Optional[bool] = None

@app.get("/api/health")
def health():
    try:
        return {"api":"ok","neo4j":verify_connection()}
    except Exception as e:
        return {"api":"ok","neo4j":False,"detail":str(e)}

@app.get("/api/summary")
def api_summary():
    try:
        return summary()
    except Exception as e:
        raise HTTPException(503, detail=str(e))

@app.get("/api/transactions")
def api_transactions(limit: int = 20):
    return list_transactions(max(1,min(limit,200)))

@app.post("/api/transactions")
def api_create(item: TransactionIn):
    try:
        return {"transaction_id":create_transaction(item.model_dump())}
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.put("/api/transactions/{transaction_id}")
def api_update(transaction_id: str, item: TransactionUpdate):
    try:
        result=update_transaction(transaction_id,item.model_dump(exclude_none=True))
        if not result: raise HTTPException(404, detail="Transaction not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.delete("/api/transactions/{transaction_id}")
def api_delete(transaction_id: str):
    try:
        return {"deleted":delete_transaction(transaction_id)}
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.get("/api/fraud/shared-devices")
def api_shared_devices(limit: int = 20):
    return shared_devices(max(1,min(limit,100)))

@app.get("/api/fraud/cycles")
def api_cycles(max_hops: int = 5, limit: int = 20):
    return cycles(max(2,min(max_hops,8)), max(1,min(limit,100)))

@app.get("/api/fraud/high-risk-accounts")
def api_high_risk(limit: int = 20):
    return high_risk_accounts(max(1,min(limit,100)))

@app.get("/api/fraud/rings")
def api_rings(limit: int = 20):
    return rings(max(1,min(limit,100)))

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
