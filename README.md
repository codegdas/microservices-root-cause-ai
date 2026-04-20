🚀 Microservices Root Cause Analysis (AI + Graph)

A Graph-powered AIOps system that detects failures across microservices, stores telemetry in Neo4j, and performs AI-driven Root Cause Analysis (RCA).

🧠 Architecture Overview
User Traffic → Gateway → Order → Payment → Inventory
↓
Logs (JSON)
↓
Elasticsearch
↓
Neo4j Graph DB
↓
RCA Agent (AI)
↓
Incident + Root Cause + Impact
🔥 Key Features
📦 Microservices simulation (Gateway, Order, Payment, Inventory)
📊 Centralized logging via Elasticsearch
🧠 Graph-based modeling in Neo4j
🚨 Automatic Alert & Incident creation
🔍 Failure propagation tracking (CALLS graph)
🤖 AI-powered Root Cause Analysis (RCA)
🔗 Impact analysis across services
🗂️ Project Structure
.
├── services/ # Microservices (gateway, order, payment, inventory)
├── ingestion/ # ES → Neo4j ingestion pipeline
├── ai/ # RCA Agent (AI + fallback logic)
├── scripts/ # Simulation + automation scripts
├── docker-compose.yml # Infrastructure setup
└── README.md
⚙️ Prerequisites
Docker & Docker Compose
Python 3.10+
Neo4j Browser (optional: Bloom for visualization)
🚀 Quick Start
1️⃣ Start all services
docker-compose up
2️⃣ Generate traffic & failures
python scripts/simulate_failure.py

👉 Run for ~10–20 seconds, then stop (CTRL + C)

3️⃣ Ingest logs into Neo4j
python -m ingestion.es_to_neo4j
4️⃣ Run RCA Agent
python -m ai.rca_agent
⚡ One-Command Pipeline (Recommended)
python -m scripts.auto_pipeline

👉 Runs:

simulate → ingest → RCA → store in graph
🧪 Verify in Neo4j

Open 👉 http://localhost:7474

Login:

neo4j / password
🔍 Queries
MATCH (s:Service) RETURN s;
MATCH (a:Alert) RETURN a;
MATCH (i:Incident) RETURN i;
MATCH (i:Incident)-[r]->(s:Service) RETURN i, r, s;
🔎 Failure Path Analysis
MATCH path =
(entry:Service)-[:CALLS*1..5]->(failing:Service)

WHERE failing.errorRate > 0.1
AND entry.errorRate < 0.05

RETURN path
🧠 RCA Output Example
Root Cause: order

Failure Chain:
payment → gateway → order

Impacted Services:
gateway, payment
📊 Graph Model
Nodes
Service
Event
Alert
Incident
Relationships
(:Service)-[:GENERATED]->(:Event)
(:Service)-[:CALLS]->(:Service)
(:Service)-[:EMITS]->(:Alert)
(:Incident)-[:ROOT_CAUSE]->(:Service)
(:Incident)-[:IMPACTS]->(:Service)
🎨 Visualization (Neo4j Bloom Recommended)

Suggested styling:

🔴 Root Cause → Red
🟠 Impacted Services → Orange
🟢 Healthy Services → Green
🔥 Incident → Bold Red
🧠 How RCA Works

1. Logs are ingested into Neo4j
2. Service metrics are computed:
   errorRate = errorCount / totalCount
3. Alerts & Incidents triggered based on thresholds
4. RCA Agent analyzes graph:
   Finds failure chain
   Identifies root cause
   Stores RCA in graph
   ⚠️ Troubleshooting
   ❌ No data in Neo4j

→ Run simulation again

python scripts/simulate_failure.py
❌ No incidents created

→ Ensure enough ERROR logs exist

❌ OpenAI quota error

→ Fallback logic will still work (no AI required)

🚀 Future Enhancements
⏱️ Real-time streaming (Kafka)
📈 Time-series anomaly detection
🧠 LLM fine-tuned RCA reasoning
📊 Dashboard (Grafana / React UI)
🔔 Slack / Email alerting
👨‍💻 Author

Ganesh Das
Neo4j Consultant | AI Enthusiast

⭐ If you like this project

Give it a ⭐ on GitHub and share!
