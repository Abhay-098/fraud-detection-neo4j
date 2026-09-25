from .database import session

def shared_devices(limit=20):
    q = """
    MATCH (d:Device)<-[:ACCESSED_FROM]-(a:Account)
    WITH d, collect(DISTINCT a.account_id) AS accounts
    WHERE size(accounts) >= 3
    RETURN d.device_id AS device, size(accounts) AS account_count,
           accounts[0..20] AS accounts
    ORDER BY account_count DESC
    LIMIT $limit
    """
    with session() as s:
        return [dict(r) for r in s.run(q, limit=int(limit))]

def cycles(max_hops=5, limit=20):
    q = """
    MATCH p=(a:Account)-[:PERFORMS]->(:Transaction)-[:SENT_TO]->(b:Account)
    WHERE a <> b
    WITH a,b
    MATCH (b)-[:PERFORMS]->(:Transaction)-[:SENT_TO]->(c:Account)
    WHERE c <> a
    RETURN a.account_id AS start_account, b.account_id AS next_account,
           c.account_id AS next2_account
    LIMIT $limit
    """
    with session() as s:
        return [dict(r) for r in s.run(q, limit=int(limit))]

def high_risk_accounts(limit=20):
    q = """
    MATCH (a:Account)
    OPTIONAL MATCH (a)-[:PERFORMS]->(t:Transaction)
    WITH a, count(t) AS tx_count,
         sum(CASE WHEN coalesce(t.is_fraud,false) THEN 1 ELSE 0 END) AS known_fraud
    OPTIONAL MATCH (a)-[:ACCESSED_FROM]->(d:Device)
    WITH a, tx_count, known_fraud, count(DISTINCT d) AS devices
    RETURN a.account_id AS account,
           tx_count, known_fraud, devices,
           (known_fraud * 5 + CASE WHEN devices > 1 THEN 2 ELSE 0 END
            + CASE WHEN tx_count > 50 THEN 1 ELSE 0 END) AS risk_indicator
    ORDER BY risk_indicator DESC, known_fraud DESC, tx_count DESC
    LIMIT $limit
    """
    with session() as s:
        return [dict(r) for r in s.run(q, limit=int(limit))]

def rings(limit=20):
    q = """
    MATCH (a:Account)-[:PERFORMS]->(t:Transaction)-[:SENT_TO]->(b:Account)
    WITH a,b,count(t) AS transfers
    WHERE transfers >= 2
    RETURN a.account_id AS account_a, b.account_id AS account_b,
           transfers
    ORDER BY transfers DESC
    LIMIT $limit
    """
    with session() as s:
        return [dict(r) for r in s.run(q, limit=int(limit))]

def summary():
    q = """
    OPTIONAL MATCH (c:Customer) WITH count(c) AS customers
    OPTIONAL MATCH (a:Account) WITH customers,count(a) AS accounts
    OPTIONAL MATCH (t:Transaction) WITH customers,accounts,count(t) AS transactions
    OPTIONAL MATCH (d:Device) WITH customers,accounts,transactions,count(d) AS devices
    OPTIONAL MATCH (m:Merchant) WITH customers,accounts,transactions,devices,count(m) AS merchants
    OPTIONAL MATCH (f:Transaction) WHERE f.is_fraud=true
    RETURN customers,accounts,transactions,devices,merchants,count(f) AS fraud_transactions
    """
    with session() as s:
        return dict(s.run(q).single())
