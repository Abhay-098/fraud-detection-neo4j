# Graph-Based Financial Fraud Detection and Fraud-Ring Detection Using Neo4j

A hybrid financial fraud detection system combining **Machine Learning** with **Neo4j graph analytics**.

The system uses a **Logistic Regression model** for transaction-level fraud prediction and **Neo4j** for relationship-aware fraud investigation, including suspicious account connections, shared devices, transaction cycles, reverse flows, and potential fraud rings.

## Live Demo

**Application:**  
https://fraud-detection-neo4j.onrender.com/

**Swagger API Documentation:**  
https://fraud-detection-neo4j.onrender.com/docs

> The application is deployed on Render and uses Neo4j AuraDB as the cloud graph database. The free hosting service may take a short time to start after a period of inactivity.

---

## Project Overview

Financial fraud is often more complex than a single suspicious transaction. Fraudulent activities may involve multiple accounts, customers, devices, merchants, and coordinated money transfers.

Traditional fraud detection models mainly analyze individual transaction attributes. This project combines transaction-level machine learning with graph-based relationship analysis.

The system consists of:

- Machine Learning fraud classification
- Neo4j graph database
- Graph-based fraud investigation
- Fraud-ring and transaction-cycle detection
- FastAPI backend
- REST APIs and CRUD operations
- Interactive investigation dashboard
- Neo4j AuraDB cloud database
- Render cloud deployment

---

## System Architecture

```text
                    PaySim Dataset
                          |
                          v
                 Data Preprocessing
                          |
               +----------+----------+
               |                     |
               v                     v
        ML Fraud Model          Neo4j AuraDB
     Logistic Regression       Graph Database
               |                     |
               |              Graph Analysis
               |              - Risk indicators
               |              - Shared devices
               |              - Reverse flows
               |              - Cycles
               |              - Fraud rings
               |                     |
               +----------+----------+
                          |
                          v
                    FastAPI Backend
                          |
                          v
                Investigation Dashboard
                          |
                          v
                   Render Deployment
```

---

## Features

### Machine Learning Fraud Detection

A trained **Logistic Regression** model is used for transaction-level fraud prediction.

The model uses:

- Transaction step
- Transaction type
- Transaction amount
- Origin account old balance
- Origin account new balance
- Destination account old balance
- Destination account new balance

The system returns:

- FRAUD / LEGITIMATE classification
- Fraud probability
- Classification threshold
- Model information
- Ground-truth comparison for stored PaySim transactions

The PaySim `is_fraud` ground-truth label is **not used as an input to the prediction**.

---

## Neo4j Graph Analysis

Neo4j is used to analyze relationships between financial entities.

The graph investigation layer supports:

- Transaction risk indicators
- High-risk account investigation
- Shared-device analysis
- Reverse money-flow detection
- Transaction-cycle detection
- Potential fraud-ring detection
- Relationship-aware investigation

Graph-risk indicators are intended to support investigation and should not automatically be interpreted as proof of fraud.

---

## Graph Data Model

### Nodes

```text
Customer
Account
Transaction
Device
Location
Merchant
```

### Relationships

```text
(Customer)-[:OWNS]->(Account)

(Account)-[:PERFORMS]->(Transaction)

(Transaction)-[:SENT_TO]->(Account)

(Customer)-[:USES]->(Device)

(Account)-[:ACCESSED_FROM]->(Device)

(Transaction)-[:OCCURRED_AT]->(Location)

(Transaction)-[:PAID_TO]->(Merchant)

(Customer)-[:LOCATED_AT]->(Location)
```

This structure allows indirect relationships between customers, accounts, transactions, devices, merchants, and locations to be investigated efficiently.

---

## Dataset

The project uses the **PaySim financial transaction dataset**.

The machine-learning model uses transaction information such as:

```text
step
type
amount
oldbalanceOrg
newbalanceOrig
oldbalanceDest
newbalanceDest
is_fraud
```

The `is_fraud` attribute is used as the target during model training and for evaluation. It is not provided as an input feature during fraud prediction.

Because PaySim does not contain all device and location information required for graph relationship demonstrations, selected device and location relationships in the cloud demonstration are **synthetic enrichments**.

These relationships are used for graph investigation and are not presented as original PaySim attributes.

---

## Machine Learning Model

The project uses **Logistic Regression** with preprocessing for numerical and categorical transaction features.

### Held-Out Evaluation

| Metric | Result |
|---|---:|
| Accuracy | 99.728% |
| Precision | 32% |
| Recall | 32% |
| F1 Score | 32% |
| ROC-AUC | 0.9747 |
| PR-AUC | 0.3228 |

Because fraud data is highly imbalanced, accuracy alone is not sufficient for evaluating the model. Precision, recall, F1, ROC-AUC, and PR-AUC are therefore considered together.

### Classification Threshold

The deployed model uses an operating classification threshold of:

```text
10%
```

The threshold was selected during deployment/integration testing to improve the precision-recall trade-off for the prototype.

---

## Fraud-Ring Detection

The graph-analysis component investigates groups of connected accounts rather than analyzing only individual transactions.

Fraud-ring indicators include:

- Shared infrastructure
- Internal money transfers
- Reciprocal money flows
- Transaction cycles
- Multiple interconnected accounts

A synthetic validation ring is included in the demonstration database to validate the structural fraud-ring detection logic.

The synthetic example contains:

```text
4 connected accounts
5 internal transfers
1,225,000 total internal transaction amount
Reciprocal money flows
Risk Score: 85/100
Risk Level: HIGH
```

The validation ring is intentionally synthetic and should not be interpreted as a naturally occurring PaySim fraud ring.

---

## Backend API

The backend is developed using **FastAPI**.

Interactive API documentation:

https://fraud-detection-neo4j.onrender.com/docs

Main API functionality includes:

```text
GET  /api/health
GET  /api/summary

GET  /api/transactions
POST /api/transactions

GET  /api/fraud/shared-devices
GET  /api/fraud/high-risk-accounts
GET  /api/fraud/cycles
GET  /api/fraud/rings

POST /api/fraud/analyze
GET  /api/fraud/analyze/{transaction_id}
```

Transaction CRUD operations are also implemented through the backend.

---

## Dashboard

The web dashboard provides:

- Neo4j database summary
- Stored transaction fraud detection
- ML fraud probability
- Neo4j graph-risk analysis
- Ground-truth comparison
- New transaction graph screening
- High-risk account indicators
- Shared-device clusters
- Potential fraud rings
- Recent transactions

The dashboard separates:

```text
ML Fraud Detection
        +
Neo4j Graph Risk Analysis
        +
Ground Truth Evaluation
```

This makes it possible to compare predictive and relationship-based evidence without using the ground-truth label as an input to prediction.

---

## Technology Stack

| Component | Technology |
|---|---|
| Graph Database | Neo4j |
| Cloud Graph Database | Neo4j AuraDB |
| Backend | FastAPI |
| Language | Python |
| Machine Learning | Scikit-learn |
| ML Model | Logistic Regression |
| Data Processing | Pandas / NumPy |
| Frontend | HTML / CSS / JavaScript |
| API Documentation | Swagger / OpenAPI |
| Deployment | Render |
| Version Control | Git / GitHub |
| Dataset | PaySim |

---

## Project Structure

```text
fraud-detection-neo4j/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── fraud_detection.py
│   └── ml_detection.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── scripts/
│   ├── prepare_paysim.py
│   ├── prepare_aura_demo.py
│   ├── load_neo4j.py
│   ├── train_baseline.py
│   ├── evaluate_fraud_detector.py
│   ├── evaluate_ml_detector.py
│   └── update_transaction_features.py
│
├── cypher/
├── data/
├── models/
├── reports/
│   └── figures/
├── tests/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Running Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Abhay-098/fraud-detection-neo4j.git
cd fraud-detection-neo4j
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Neo4j

Create a `.env` file using `.env.example`.

```env
NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=your_username
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=your_database
```

Do not commit database credentials or the `.env` file.

### 4. Start the Application

```bash
python -m uvicorn backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Cloud Deployment

The deployed architecture is:

```text
Web Dashboard
      |
      v
FastAPI Backend
      |
      v
    Render
      |
      v
Neo4j AuraDB
```

### Live Application

https://fraud-detection-neo4j.onrender.com/

### API Documentation

https://fraud-detection-neo4j.onrender.com/docs

---

## Limitations

- PaySim is a simulated financial transaction dataset.
- Device and location relationships used in selected graph demonstrations are synthetic enrichments.
- Graph-risk indicators identify suspicious structures but do not prove fraud.
- The current machine-learning classifier is a Logistic Regression baseline.
- Financial fraud data is highly imbalanced.
- The 10% classification threshold was selected for the prototype's deployment/integration configuration.
- Current cycle analysis focuses on implemented 3-account and 4-account cycle patterns.
- The prototype currently analyzes historical data rather than a real-time financial transaction stream.

---

## Future Improvements

- Real-time transaction streaming
- Apache Kafka integration
- Graph Neural Networks
- Advanced community detection
- Temporal graph analysis
- Real-world device/IP information
- Dynamic fraud-ring detection
- Automated fraud alerts
- Investigator case management
- Explainable AI
- Larger-scale performance testing

---

## Conclusion

This project demonstrates how **machine learning and graph databases can complement each other for financial fraud detection**.

The machine-learning component provides transaction-level fraud prediction, while Neo4j provides relationship-aware investigation of accounts, transactions, shared infrastructure, transaction cycles, and potential fraud rings.

The final architecture combines:

```text
Transaction
   |
   +---- Machine Learning
   |        |
   |        +---- Fraud Probability
   |        +---- FRAUD / LEGITIMATE
   |
   +---- Neo4j Graph Analysis
            |
            +---- Risk Indicators
            +---- Shared Infrastructure
            +---- Reverse Flows
            +---- Transaction Cycles
            +---- Fraud-Ring Investigation
```

Together, these components provide an end-to-end fraud detection and investigation prototype with a graph database, machine-learning model, backend APIs, CRUD operations, web dashboard, cloud database, and web deployment.

---

## Links

**Live Application:**  
https://fraud-detection-neo4j.onrender.com/

**Swagger API Documentation:**  
https://fraud-detection-neo4j.onrender.com/docs

**GitHub Repository:**  
https://github.com/Abhay-098/fraud-detection-neo4j