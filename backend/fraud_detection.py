from .database import session
from .ml_detection import predict_fraud


def _clamp(value, low=0, high=100):
    return max(low, min(high, int(round(value))))


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
    """
    Detect circular money-flow patterns between accounts.

    Supports 3-account and 4-account cycles.
    PaySim fraud labels are not used for detection.
    """

    max_hops = int(max_hops)
    limit = int(limit)

    # -------------------------
    # 3-account cycles
    # A -> B -> C -> A
    # -------------------------
    q3 = """
    MATCH (a:Account)-[:PERFORMS]->(t1:Transaction)-[:SENT_TO]->(b:Account),
          (b)-[:PERFORMS]->(t2:Transaction)-[:SENT_TO]->(c:Account),
          (c)-[:PERFORMS]->(t3:Transaction)-[:SENT_TO]->(a)

    WHERE a <> b
      AND b <> c
      AND c <> a
      AND a.account_id < b.account_id
      AND a.account_id < c.account_id

    RETURN
        '3-account-cycle' AS cycle_type,

        [
            a.account_id,
            b.account_id,
            c.account_id
        ] AS accounts,

        [
            t1.transaction_id,
            t2.transaction_id,
            t3.transaction_id
        ] AS transactions,

        3 AS hop_count,

        round(
            coalesce(t1.amount, 0) +
            coalesce(t2.amount, 0) +
            coalesce(t3.amount, 0),
            2
        ) AS cycle_amount

    ORDER BY cycle_amount DESC
    LIMIT $limit
    """

    # -------------------------
    # 4-account cycles
    # A -> B -> C -> D -> A
    # -------------------------
    q4 = """
    MATCH (a:Account)-[:PERFORMS]->(t1:Transaction)-[:SENT_TO]->(b:Account),
          (b)-[:PERFORMS]->(t2:Transaction)-[:SENT_TO]->(c:Account),
          (c)-[:PERFORMS]->(t3:Transaction)-[:SENT_TO]->(d:Account),
          (d)-[:PERFORMS]->(t4:Transaction)-[:SENT_TO]->(a)

    WHERE a <> b
      AND a <> c
      AND a <> d
      AND b <> c
      AND b <> d
      AND c <> d

      AND a.account_id < b.account_id
      AND a.account_id < c.account_id
      AND a.account_id < d.account_id

    RETURN
        '4-account-cycle' AS cycle_type,

        [
            a.account_id,
            b.account_id,
            c.account_id,
            d.account_id
        ] AS accounts,

        [
            t1.transaction_id,
            t2.transaction_id,
            t3.transaction_id,
            t4.transaction_id
        ] AS transactions,

        4 AS hop_count,

        round(
            coalesce(t1.amount, 0) +
            coalesce(t2.amount, 0) +
            coalesce(t3.amount, 0) +
            coalesce(t4.amount, 0),
            2
        ) AS cycle_amount

    ORDER BY cycle_amount DESC
    LIMIT $limit
    """

    results = []

    with session() as s:

        if max_hops >= 3:
            results.extend(
                dict(r)
                for r in s.run(q3, limit=limit)
            )

        if max_hops >= 4:
            results.extend(
                dict(r)
                for r in s.run(q4, limit=limit)
            )

    # Highest-value circular flows first
    results.sort(
        key=lambda x: x.get("cycle_amount", 0),
        reverse=True
    )

    return results[:limit]


def high_risk_accounts(limit=20):
    # This is an investigation ranking. known_fraud is displayed only as
    # ground truth/evaluation evidence; it is NOT used in risk_indicator.
    q = """
    MATCH (a:Account)
    OPTIONAL MATCH (a)-[:PERFORMS]->(t:Transaction)
    WITH a, count(t) AS tx_count,
         sum(CASE WHEN coalesce(t.is_fraud,false) THEN 1 ELSE 0 END) AS known_fraud,
         sum(coalesce(t.amount,0)) AS total_amount
    OPTIONAL MATCH (a)-[:ACCESSED_FROM]->(d:Device)<-[:ACCESSED_FROM]-(peer:Account)
    WHERE peer <> a
    WITH a, tx_count, known_fraud, total_amount,
         count(DISTINCT d) AS devices,
         count(DISTINCT peer) AS shared_device_peers
    RETURN a.account_id AS account, tx_count, known_fraud, devices,
           shared_device_peers, round(total_amount,2) AS total_amount,
           (CASE WHEN shared_device_peers >= 10 THEN 4 WHEN shared_device_peers >= 3 THEN 2 ELSE 0 END
            + CASE WHEN tx_count >= 20 THEN 2 WHEN tx_count >= 5 THEN 1 ELSE 0 END
            + CASE WHEN total_amount >= 1000000 THEN 2 WHEN total_amount >= 100000 THEN 1 ELSE 0 END) AS risk_indicator
    ORDER BY risk_indicator DESC, shared_device_peers DESC, total_amount DESC
    LIMIT $limit
    """
    with session() as s:
        return [dict(r) for r in s.run(q, limit=int(limit))]


def rings(limit=20):
    """
    Detect candidate fraud rings using multiple graph signals.

    IMPORTANT:
    - Shared-device membership alone is NOT considered a fraud ring.
    - PaySim is_fraud is returned only as evaluation evidence.
    - is_fraud is NOT used to calculate ring_score.

    A candidate ring must contain:
      1. Multiple accounts sharing infrastructure, AND
      2. Actual money movement between those accounts.

    Additional evidence such as reciprocal transfers increases the score.
    """

    q = """
    MATCH (dev:Device)<-[:ACCESSED_FROM]-(a:Account)
    WITH dev, collect(DISTINCT a) AS members
    WHERE size(members) >= 3

    UNWIND members AS src

    MATCH (src)-[:PERFORMS]->(t:Transaction)-[:SENT_TO]->(dst:Account)
    WHERE dst IN members
      AND dst <> src

    WITH dev,
         members,
         collect(DISTINCT t) AS internal_txs,
         collect(DISTINCT src.account_id + '->' + dst.account_id) AS flows,
         count(DISTINCT t) AS internal_transfers,
         sum(coalesce(t.amount, 0)) AS internal_amount

    // A shared device by itself is NOT enough.
    WHERE internal_transfers > 0

    UNWIND internal_txs AS tx

    WITH dev,
         members,
         internal_txs,
         flows,
         internal_transfers,
         internal_amount,
         sum(
             CASE
                 WHEN coalesce(tx.is_fraud, false) THEN 1
                 ELSE 0
             END
         ) AS known_fraud_transactions

    // Detect reciprocal movement A->B and B->A.
    WITH dev,
         members,
         internal_txs,
         flows,
         internal_transfers,
         internal_amount,
         known_fraud_transactions,
         size([
             flow IN flows
             WHERE split(flow, '->')[1] + '->' +
                   split(flow, '->')[0] IN flows
         ]) AS reciprocal_flow_matches

    WITH dev,
         members,
         internal_transfers,
         internal_amount,
         known_fraud_transactions,
         reciprocal_flow_matches,
         size(members) AS member_count,

         // Explainable score.
         // Ground-truth fraud labels are deliberately excluded.
         (
             25

             + CASE
                 WHEN internal_transfers >= 10 THEN 30
                 WHEN internal_transfers >= 5 THEN 25
                 WHEN internal_transfers >= 2 THEN 20
                 ELSE 10
               END

             + CASE
                 WHEN internal_amount >= 1000000 THEN 20
                 WHEN internal_amount >= 500000 THEN 15
                 WHEN internal_amount >= 100000 THEN 10
                 ELSE 5
               END

             + CASE
                 WHEN reciprocal_flow_matches >= 4 THEN 20
                 WHEN reciprocal_flow_matches >= 2 THEN 15
                 WHEN reciprocal_flow_matches >= 1 THEN 10
                 ELSE 0
               END

             + CASE
                 WHEN size(members) >= 10 THEN 5
                 WHEN size(members) >= 5 THEN 3
                 ELSE 0
               END
         ) AS raw_score

    WITH dev,
         members,
         member_count,
         internal_transfers,
         internal_amount,
         known_fraud_transactions,
         reciprocal_flow_matches,
         CASE
             WHEN raw_score > 100 THEN 100
             ELSE raw_score
         END AS ring_score

    RETURN
         dev.device_id AS ring_id,

         member_count,

         [m IN members | m.account_id][0..20] AS accounts,

         internal_transfers,

         round(coalesce(internal_amount, 0), 2)
             AS internal_amount,

         reciprocal_flow_matches,

         ring_score,

         CASE
             WHEN ring_score >= 75 THEN 'HIGH'
             WHEN ring_score >= 50 THEN 'MEDIUM'
             ELSE 'LOW'
         END AS risk_level,

         ['shared_infrastructure',
          'internal_money_flows']

         + CASE
             WHEN reciprocal_flow_matches > 0
             THEN ['reciprocal_money_flow']
             ELSE []
           END

         AS indicators,

         {
             known_fraud_transactions:
                 known_fraud_transactions,

             used_in_score:
                 false
         } AS ground_truth_evaluation

    ORDER BY
         ring_score DESC,
         internal_transfers DESC,
         internal_amount DESC

    LIMIT $limit
    """

    with session() as s:
        return [
            dict(r)
            for r in s.run(q, limit=int(limit))
        ]


def analyze_transaction(origin, destination, amount, tx_type="TRANSFER"):
    """Explainable fraud-risk analysis without using the PaySim label.

    Score (0-100): amount anomaly 25, balance-drain 20, shared-device
    exposure 20, account activity 10, risky transaction type 10, graph
    proximity/circular return path 15. Ground truth is returned separately
    when the exact stored transaction is analyzed elsewhere.
    """
    q = """
    OPTIONAL MATCH (o:Account {account_id:$origin})
    OPTIONAL MATCH (d:Account {account_id:$destination})
    OPTIONAL MATCH (o)-[:PERFORMS]->(ot:Transaction)
    WITH o,d, count(DISTINCT ot) AS origin_tx_count,
         max(coalesce(ot.amount,0)) AS origin_max_amount,
         avg(coalesce(ot.amount,0)) AS origin_avg_amount,
         max(coalesce(ot.oldbalanceOrg,0)) AS observed_balance
    OPTIONAL MATCH (o)-[:ACCESSED_FROM]->(dev:Device)<-[:ACCESSED_FROM]-(peer:Account)
    WHERE peer <> o
    WITH o,d,origin_tx_count,origin_max_amount,origin_avg_amount,observed_balance,
         count(DISTINCT peer) AS shared_device_peers,
         collect(DISTINCT dev.device_id)[0..10] AS shared_devices
    OPTIONAL MATCH (d)-[:PERFORMS]->(rt:Transaction)-[:SENT_TO]->(o)
    WITH o,d,origin_tx_count,origin_max_amount,origin_avg_amount,observed_balance,
        shared_device_peers,shared_devices,count(rt) AS return_flows
    RETURN o IS NOT NULL AS origin_found,
        d IS NOT NULL AS destination_found,
        origin_tx_count, origin_max_amount, origin_avg_amount, observed_balance,
        shared_device_peers, shared_devices, return_flows
    """
    with session() as s:
        rec = dict(s.run(q, origin=origin, destination=destination).single())

    amount = float(amount)
    score = 0
    indicators = []
    evidence = {
        "origin_found": rec.get("origin_found", False),
        "destination_found": rec.get("destination_found", False),
        "origin_tx_count": rec.get("origin_tx_count", 0),
        "shared_device_peers": rec.get("shared_device_peers", 0),
        "shared_devices": rec.get("shared_devices", []),
        "return_flows": rec.get("return_flows", 0),
    }

    avg_amount = float(rec.get("origin_avg_amount") or 0)
    max_amount = float(rec.get("origin_max_amount") or 0)
    observed_balance = float(rec.get("observed_balance") or 0)

    # Amount anomaly: compare with account history when available, otherwise
    # use conservative PaySim-scale thresholds.
    if avg_amount > 0 and amount >= max(avg_amount * 4, 100000):
        score += 25; indicators.append("amount_far_above_origin_history")
    elif amount >= 500000:
        score += 25; indicators.append("very_large_transaction_amount")
    elif amount >= 100000:
        score += 15; indicators.append("large_transaction_amount")

    # Balance draining signal if balance history exists on imported data.
    if observed_balance > 0 and amount / observed_balance >= 0.9:
        score += 20; indicators.append("possible_balance_draining")

    # Device relationships in the Aura demo are synthetic.
    # Keep them as graph evidence, but do not use them in the
    # PaySim transaction fraud-risk score.
    peers = int(rec.get("shared_device_peers") or 0)

    tx_count = int(rec.get("origin_tx_count") or 0)
    if tx_count >= 20:
        score += 10; indicators.append("high_origin_transaction_activity")
    elif tx_count >= 5:
        score += 5; indicators.append("elevated_origin_transaction_activity")

    if str(tx_type).upper() in {"TRANSFER", "CASH_OUT"}:
        score += 10; indicators.append("higher_risk_transaction_type")

    if int(rec.get("return_flows") or 0) > 0:
        score += 15; indicators.append("reverse_money_flow_between_accounts")

    score = _clamp(score)
    level = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
    return {
        "origin": origin,
        "destination": destination,
        "amount": amount,
        "type": str(tx_type).upper(),
        "risk_score": score,
        "risk_level": level,
        "flagged": score >= 70,
        "indicators": indicators or ["no_strong_indicator_detected"],
        "evidence": evidence,
        "note": "Risk indicators support investigation; they are not proof of fraud. PaySim is_fraud labels are not used to calculate this score."
    }


def analyze_stored_transaction(transaction_id):
    q = """
    MATCH (o:Account)-[:PERFORMS]->(t:Transaction {transaction_id:$transaction_id})-[:SENT_TO]->(d:Account)
    RETURN
        o.account_id AS origin,
        d.account_id AS destination,
        t.step AS step,
        t.amount AS amount,
        t.type AS type,
        t.oldbalanceOrg AS oldbalanceOrg,
        t.newbalanceOrig AS newbalanceOrig,
        t.oldbalanceDest AS oldbalanceDest,
        t.newbalanceDest AS newbalanceDest,
        coalesce(t.is_fraud, false) AS known_label
    """

    with session() as s:
        rec = s.run(
            q,
            transaction_id=transaction_id
        ).single()

    if not rec:
        return None

    rec = dict(rec)

    # Existing Neo4j graph/rule analysis
    graph_result = analyze_transaction(
        rec["origin"],
        rec["destination"],
        rec.get("amount") or 0,
        rec.get("type") or "TRANSFER",
    )

    # Machine-learning prediction
    ml_result = predict_fraud({
        "step": rec.get("step") or 0,
        "type": rec.get("type") or "TRANSFER",
        "amount": rec.get("amount") or 0,
        "oldbalanceOrg": rec.get("oldbalanceOrg") or 0,
        "newbalanceOrig": rec.get("newbalanceOrig") or 0,
        "oldbalanceDest": rec.get("oldbalanceDest") or 0,
        "newbalanceDest": rec.get("newbalanceDest") or 0,
    })

    return {
        "transaction_id": transaction_id,

        "transaction": {
            "origin": rec["origin"],
            "destination": rec["destination"],
            "step": rec.get("step"),
            "type": rec.get("type"),
            "amount": rec.get("amount"),
        },

        "ml_analysis": ml_result,

        "graph_analysis": graph_result,

        "ground_truth": {
            "is_fraud": bool(rec.get("known_label")),
            "used_in_prediction": False,
        },
    }


def summary():
    q = """
    OPTIONAL MATCH (c:Customer) WITH count(c) AS customers
    OPTIONAL MATCH (a:Account) WITH customers,count(a) AS accounts
    OPTIONAL MATCH (t:Transaction) WITH customers,accounts,count(t) AS transactions
    OPTIONAL MATCH (d:Device) WITH customers,accounts,transactions,count(d) AS devices
    OPTIONAL MATCH (m:Merchant) WITH customers,accounts,transactions,devices,count(m) AS merchants
    OPTIONAL MATCH (f:Transaction) WHERE coalesce(f.is_fraud,false)=true
    RETURN customers,accounts,transactions,devices,merchants,count(f) AS fraud_transactions
    """
    with session() as s:
        return dict(s.run(q).single())
