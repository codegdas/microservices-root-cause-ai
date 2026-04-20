# 🧠 AI-Powered Root Cause Analysis using Graph + Logs

## 📌 Overview

This project demonstrates a **real-time Root Cause Analysis (RCA) system** for microservices using:

- 🧱 Microservices (Flask)
- 📊 Elasticsearch (log storage)
- 🔗 Neo4j (graph modeling)
- 🤖 AI (OpenAI) + fallback logic
- 🔄 Automated pipeline

---

## 🎯 Problem Statement

In distributed systems, failures propagate across multiple services.

👉 Identifying the **root cause quickly** is difficult using traditional logs.

---

## 💡 Solution

We convert logs into a **graph of relationships** and use:

- Graph-based reasoning
- AI (OpenAI) fallback system

To identify:

- Root cause service
- Failure propagation chain
- Impacted services

---

## 🧠 One-Line Summary

> Convert logs into relationships and use AI + graph to find root causes faster.

---

## 🏗️ Architecture

Microservices → Logs → Elasticsearch → Neo4j → RCA Engine → Incident Graph

---

## 📂 Project Structure

microservices-root-cause-ai/
│
├── services/ # Microservices (gateway, order, payment, inventory)
├── ingestion/ # ES → Neo4j pipeline
├── ai/ # RCA logic (AI + fallback)
├── scripts/ # Automation scripts
├── graph/ # Schema & queries
├── elk/ # Elasticsearch setup
├── docker-compose.yml
└── README.md

---

## ⚙️ Prerequisites

- Docker & Docker Compose
- Python 3.9+
- pip

---

## 🚀 How to Run This Project (Step-by-Step)

Follow these steps exactly 👇

---

### 🔹 Step 1: Clone Repository

````bash
git clone <your-repo-url>
cd microservices-root-cause-ai
🔹 Step 2: Start Infrastructure
docker-compose up --build

This starts:

Service	URL
Gateway	http://localhost:5001

Elasticsearch	http://localhost:9200

Neo4j Browser	http://localhost:7474

Neo4j Login:

username: neo4j
password: password
🔹 Step 3: Install Dependencies
pip install -r ingestion/requirements.txt
pip install openai neo4j requests
🔹 Step 4: (Optional) Add OpenAI API Key
export OPENAI_API_KEY="your-api-key"

If not set → system uses fallback RCA logic

🔹 Step 5: Generate Traffic (Simulate Failures)

Open a new terminal:

python scripts/simulate_failure.py

You will see:

🚀 Sending request...
❌ Failure detected
🔹 Step 6: Run Automated Pipeline

Open another terminal:

python -m scripts.auto_pipeline
🔹 Step 7: Observe RCA Output
🤖 RCA RESULT:

Root Cause: order
Failure Chain: payment → gateway → order
Impacted Services: gateway, payment
🔹 Step 8: View Results in Neo4j

Open:

👉 http://localhost:7474

Run:

MATCH (i:Incident)
RETURN i.rootCause, i.failureChain, i.rca
ORDER BY i.createdAt DESC
🔁 Full Execution Flow
Terminal 1 → docker-compose up
Terminal 2 → simulate_failure.py
Terminal 3 → auto_pipeline.py
🔄 How It Works
Microservices generate logs
Logs are stored in Elasticsearch
Ingestion service pushes logs → Neo4j
Graph is built (Service → Event)
RCA engine analyzes failures
Incident is created and stored in Neo4j
🧠 RCA Logic
🔹 AI Mode

Uses OpenAI to:

Analyze logs
Identify root cause
Generate explanation
🔹 Fallback Mode (Graph-Based)
Filters ERROR logs
Sorts by timestamp
Identifies earliest failure
Builds failure chain
📊 Graph Model
Nodes
Service
Event
Incident
Relationships
(Service)-[:GENERATED]->(Event)
(Incident)-[:ROOT_CAUSE]->(Service)
(Incident)-[:IMPACTED]->(Service)
🔍 Example RCA Output
Root Cause: order

Failure Chain:
payment → gateway → order

Impacted Services:
gateway, payment
🎯 Features
✅ Real-time failure simulation
✅ Log ingestion pipeline
✅ Graph-based modeling
✅ AI-driven RCA
✅ Fallback RCA (no AI dependency)
✅ Automated pipeline
✅ Incident storage in Neo4j
📈 Query RCA in Neo4j
MATCH (i:Incident)
RETURN i.rootCause, i.failureChain, i.rca
ORDER BY i.createdAt DESC
🧠 Key Learnings
Graph databases for observability
Failure propagation modeling
AI + deterministic hybrid systems
Event-driven architecture
Designing resilient systems
🚀 Future Improvements
🔥 UI Dashboard
🔥 Real-time alerts (Slack/Email)
🔥 Kubernetes integration
🔥 Distributed tracing
🔥 Time-window based RCA
💼 Resume Highlight

Built an automated AI-driven root cause analysis system using Elasticsearch, Neo4j, and OpenAI to detect failure propagation across microservices with fallback graph-based reasoning.

🧑‍💻 Author

Ganesh Das
Neo4j Consultant | AI Enthusiast

⭐ If you like this project

Give it a star ⭐ on GitHub!


---

# 💥 This README Gives You

```text
✔ Clear setup instructions
✔ Step-by-step run guide
✔ Architecture clarity
✔ Strong resume impact
✔ Interview-ready explanation
````
