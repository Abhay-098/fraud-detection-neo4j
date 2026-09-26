from .database import session

def list_transactions(limit=20):
    q = """
    MATCH (o:Account)-[:PERFORMS]->(t:Transaction)-[:SENT_TO]->(d:Account)
    RETURN t.transaction_id AS transaction_id, t.step AS step,
           t.type AS type, t.amount AS amount, coalesce(t.is_fraud,false) AS is_fraud,
           coalesce(t.origin,o.account_id) AS origin,
           coalesce(t.destination,d.account_id) AS destination
    ORDER BY t.step DESC
    LIMIT $limit
    """
    with session() as s: return [dict(r) for r in s.run(q, limit=int(limit))]

def create_transaction(data):
    q = """
    MERGE (o:Customer {customer_id:$origin})
    MERGE (oa:Account {account_id:$origin})
    MERGE (o)-[:OWNS]->(oa)
    MERGE (d:Customer {customer_id:$destination})
    MERGE (da:Account {account_id:$destination})
    MERGE (d)-[:OWNS]->(da)
    CREATE (t:Transaction {transaction_id:$transaction_id, step:$step, type:$type,
      amount:$amount, origin:$origin, destination:$destination, is_fraud:$is_fraud})
    CREATE (oa)-[:PERFORMS]->(t)
    CREATE (t)-[:SENT_TO]->(da)
    RETURN t.transaction_id AS transaction_id
    """
    with session() as s: return s.run(q, **data).single()["transaction_id"]

def update_transaction(transaction_id, data):
    q = """
    MATCH (t:Transaction {transaction_id:$transaction_id})
    SET t.amount=coalesce($amount,t.amount), t.type=coalesce($type,t.type),
        t.is_fraud=coalesce($is_fraud,t.is_fraud)
    RETURN t.transaction_id AS transaction_id
    """
    params={"transaction_id":transaction_id,"amount":data.get("amount"),"type":data.get("type"),"is_fraud":data.get("is_fraud")}
    with session() as s:
        rec=s.run(q, **params).single(); return dict(rec) if rec else None

def delete_transaction(transaction_id):
    q = "MATCH (t:Transaction {transaction_id:$transaction_id}) WITH t, 1 AS n DETACH DELETE t RETURN n AS deleted"
    with session() as s:
        rec=s.run(q, transaction_id=transaction_id).single(); return rec["deleted"] if rec else 0
