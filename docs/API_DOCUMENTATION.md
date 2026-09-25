# API Documentation

Base URL: `http://127.0.0.1:8000`

## Health

`GET /api/health`

Returns API and Neo4j connectivity status.

## Summary

`GET /api/summary`

Returns counts for customers, accounts, transactions, suspicious transactions, devices and merchants.

## Transactions

`GET /api/transactions?limit=20`

Returns recent transactions.

`POST /api/transactions`

Creates a transaction.

Example:

```json
{
  "transaction_id": "T-DEMO-001",
  "step": 100,
  "type": "TRANSFER",
  "amount": 12500,
  "origin": "C123",
  "destination": "C456",
  "is_fraud": false
}
```

`PUT /api/transactions/{transaction_id}`

Updates a transaction.

`DELETE /api/transactions/{transaction_id}`

Deletes a transaction.

## Fraud analysis

`GET /api/fraud/shared-devices`

Finds devices linked to multiple accounts.

`GET /api/fraud/cycles?max_hops=5`

Finds short account cycles.

`GET /api/fraud/high-risk-accounts?limit=20`

Returns accounts ranked by a transparent graph risk indicator.

`GET /api/fraud/rings`

Returns connected suspicious account groups.

## Notes

The API exposes investigation-oriented indicators. It does not claim that a graph pattern is definitive proof of fraud.
