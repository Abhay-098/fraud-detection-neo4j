import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DB = os.getenv("NEO4J_DATABASE")

CSV_PATH = Path("data/aura_demo/paysim_aura_demo.csv")


def update_batch(tx, rows):
    query = """
    UNWIND $rows AS row

    MATCH (t:Transaction {transaction_id: row.transaction_id})

    SET
        t.oldbalanceOrg = row.oldbalanceOrg,
        t.newbalanceOrig = row.newbalanceOrig,
        t.oldbalanceDest = row.oldbalanceDest,
        t.newbalanceDest = row.newbalanceDest

    RETURN count(t) AS updated
    """

    result = tx.run(query, rows=rows).single()
    return result["updated"]


def main():
    df = pd.read_csv(CSV_PATH)

    required = [
        "transaction_id",
        "oldbalanceOrg",
        "newbalanceOrig",
        "oldbalanceDest",
        "newbalanceDest",
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(
            f"Missing CSV columns: {missing}"
        )

    driver = GraphDatabase.driver(
        URI,
        auth=(USER, PASSWORD)
    )

    batch_size = 1000
    total_updated = 0

    with driver.session(database=DB) as session:

        for start in range(0, len(df), batch_size):

            batch = df.iloc[
                start:start + batch_size
            ]

            rows = []

            for _, r in batch.iterrows():
                rows.append({
                    "transaction_id": str(r["transaction_id"]),
                    "oldbalanceOrg": float(r["oldbalanceOrg"]),
                    "newbalanceOrig": float(r["newbalanceOrig"]),
                    "oldbalanceDest": float(r["oldbalanceDest"]),
                    "newbalanceDest": float(r["newbalanceDest"]),
                })

            updated = session.execute_write(
                update_batch,
                rows
            )

            total_updated += updated

            print(
                f"Processed {min(start + batch_size, len(df))}/{len(df)} "
                f"| Updated: {total_updated}"
            )

    driver.close()

    print("\nUpdate complete.")
    print(f"Transactions updated: {total_updated}")


if __name__ == "__main__":
    main()