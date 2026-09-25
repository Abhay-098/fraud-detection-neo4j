// 1. Shared devices
MATCH (d:Device)<-[:ACCESSED_FROM]-(a:Account)
WITH d, collect(DISTINCT a.account_id) AS accounts
WHERE size(accounts) >= 3
RETURN d.device_id AS device, size(accounts) AS linked_accounts, accounts
ORDER BY linked_accounts DESC;

// 2. Accounts with high transaction degree
MATCH (a:Account)-[:PERFORMS]->(t:Transaction)
RETURN a.account_id AS account, count(t) AS transaction_count
ORDER BY transaction_count DESC
LIMIT 20;

// 3. Direct account cycles (2-hop reciprocal flow)
MATCH (a:Account)-[:PERFORMS]->(t1:Transaction)-[:SENT_TO]->(b:Account),
      (b)-[:PERFORMS]->(t2:Transaction)-[:SENT_TO]->(a)
WHERE t1.transaction_id <> t2.transaction_id
RETURN a.account_id AS account_a, b.account_id AS account_b,
       t1.transaction_id AS tx1, t2.transaction_id AS tx2
LIMIT 50;

// 4. Potential fraud rings: repeated money movement between the same pair
MATCH (a:Account)-[:PERFORMS]->(t:Transaction)-[:SENT_TO]->(b:Account)
WITH a,b,count(t) AS transfers,sum(t.amount) AS total_amount
WHERE transfers >= 2
RETURN a.account_id AS account_a,b.account_id AS account_b,
       transfers,total_amount
ORDER BY transfers DESC;

// 5. Known fraud connected accounts
MATCH (a:Account)-[:PERFORMS]->(t:Transaction)
WHERE t.is_fraud=true
RETURN a.account_id AS account, count(t) AS known_fraud_transactions
ORDER BY known_fraud_transactions DESC;

// 6. Multi-hop path investigation
MATCH p=(a:Account)-[:PERFORMS]->(:Transaction)-[:SENT_TO]->(b:Account)
          -[:PERFORMS]->(:Transaction)-[:SENT_TO]->(c:Account)
WHERE a <> c
RETURN a.account_id AS source, b.account_id AS intermediary,
       c.account_id AS destination, length(p) AS path_length
LIMIT 50;
