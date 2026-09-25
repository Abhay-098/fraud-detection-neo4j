from .database import session

def list_transactions(limit=20):
    q = """
    MATCH (t:Transaction)
    RETURN t.transaction_id AS transaction_id, t.step AS step,
           t.type AS type, t.amount AS amount, t.is_fraud AS is_fraud,
           t.origin AS origin, t.destination AS destination
    ORDER BY t.step DESC
    LIMIT $limit
    """
    with session() as s:
        return [dict(r) for r in s.run(q, limit=int(limit))]

def create_transaction(data):
    q = """
    MERGE (o:Customer {customer_id:$origin})
    MERGE (oa:Account {account_id:'ACC_'+$origin})
    MERGE (o)-[:OWNS]->(oa)
    MERGE (d:Customer {customer_id:$destination})
    MERGE (da:Account {account_id:'ACC_'+$destination})
    MERGE (d)-[:OWNS]->(da)
    CREATE (t:Transaction {
      transaction_id:$transaction_id, step:$step, type:$type,
      amount:$amount, origin:$origin, destination:$destination,
      is_fraud:$is_fraud
    })
    CREATE (oa)-[:PERFORMS]->(t)
    CREATE (t)-[:SENT_TO]->(da)
    RETURN t.transaction_id AS transaction_id
    """
    with session() as s:
        return s.run(q, **data).single()["transaction_id"]

def update_transaction(transaction_id, data):
    q = """
    MATCH (t:Transaction {transaction_id:$transaction_id})
    SET t.amount=coalesce($amount,t.amount),
        t.type=coalesce($type,t.type),
        t.is_fraud=coalesce($is_fraud,t.is_fraud)
    RETURN t.transaction_id AS transaction_id
    """
    with session() as s:
        rec=s.run(q, transaction_id=transaction_id, **data).single()
        return dict(rec) if rec else None

def delete_transaction(transaction_id):
    q = """
    MATCH (t:Transaction {transaction_id:$transaction_id})
    DETACH DELETE t
    RETURN count(t) AS deleted
    """
    with session() as s:
        return s.run(q, transaction_id=transaction_id).single()["deleted"]
