# Microservices Root Cause AI

A small demo project that simulates failures across microservices and performs graph-based root cause analysis using Neo4j.

Flow:

`gateway -> order -> payment -> inventory`

Logs are sent to Elasticsearch, ingested into Neo4j, and then analyzed by the RCA agent to identify:

- root cause service
- impacted services
- related deployment or database context

## Run The Project

### 1. Start the services

```bash
docker-compose up --build
```

This starts:

- gateway
- order
- payment
- inventory
- Elasticsearch
- Neo4j

### 2. Generate traffic and failures

In a new terminal:

```bash
python scripts/simulate_failure.py
```

Let it run for a few seconds, then stop it.

### 3. Ingest logs into Neo4j

```bash
python -m ingestion.es_to_neo4j
```

### 4. Run root cause analysis

```bash
python -m ai.rca_agent
```

## Neo4j

Open [http://localhost:7474](http://localhost:7474)

Login:

- username: `neo4j`
- password: `password`

## Useful Cypher Queries

### View incidents with root cause and impact

```cypher
MATCH (i:Incident)-[:ROOT_CAUSE]->(root:Service)
OPTIONAL MATCH (i)-[:IMPACTS]->(impacted:Service)
RETURN
  i.traceId,
  root.name AS rootCause,
  collect(DISTINCT impacted.name) AS impactedServices,
  i.rca
ORDER BY i.updatedAt DESC
LIMIT 10
```

### View one trace timeline

```cypher
MATCH (s:Service)-[:GENERATED]->(e:Event {traceId: "YOUR_TRACE_ID"})
RETURN s.name AS service, e.level AS level, e.message AS message, e.timestamp AS timestamp
ORDER BY e.timestamp ASC
```

### View one incident with deployment and database context

```cypher
MATCH (i:Incident {traceId: "YOUR_TRACE_ID"})-[:ROOT_CAUSE]->(root:Service)
OPTIONAL MATCH (i)-[:IMPACTS]->(impacted:Service)
OPTIONAL MATCH (i)-[:RELATED_DEPLOYMENT]->(d:Deployment)
OPTIONAL MATCH (i)-[:RELATED_DATABASE]->(db:Database)
RETURN
  i.traceId,
  root.name AS rootCause,
  collect(DISTINCT impacted.name) AS impactedServices,
  collect(DISTINCT d.id) AS deployments,
  collect(DISTINCT db.name) AS databases,
  i.rca
```

### View failure propagation path

```cypher
MATCH (s:Service)-[:GENERATED]->(e:Event {traceId: "YOUR_TRACE_ID"})
MATCH path = (entry:Service)-[:CALLS*1..5]->(s)
RETURN
  e.id AS eventId,
  s.name AS failedService,
  [n IN nodes(path) | n.name] AS failureChain,
  path
ORDER BY length(path) DESC
LIMIT 1
```
