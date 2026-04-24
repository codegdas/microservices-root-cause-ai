# rca_agent.py

import json
import os

from neo4j import GraphDatabase

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def get_failed_traces():
    query = """
    MATCH (e:Event)
    WHERE e.level = "ERROR" AND e.traceId IS NOT NULL
    RETURN e.traceId AS traceId, count(*) AS errors
    ORDER BY errors DESC
    LIMIT 5
    """

    with driver.session() as session:
        return [r["traceId"] for r in session.run(query)]


def fetch_trace(trace_id):
    query = """
    MATCH (s:Service)-[:GENERATED]->(e:Event {traceId: $traceId})
    OPTIONAL MATCH (d:Deployment)-[:RELATED_TO]->(e)
    OPTIONAL MATCH (db:Database)-[:GENERATED]->(e)
    RETURN s.name AS service, e.level AS level, e.timestamp AS ts
        , e.message AS message
        , e.causeType AS causeType
        , d.id AS deploymentId
        , d.version AS deploymentVersion
        , db.name AS databaseName
    ORDER BY ts ASC
    """

    with driver.session() as session:
        return [dict(r) for r in session.run(query, {"traceId": trace_id})]


def build_context(trace_id, data):
    chain = list(dict.fromkeys(d["service"] for d in data))
    timeline = [
        {
            "service": d["service"],
            "level": d["level"],
            "message": d.get("message"),
            "timestamp": d.get("ts"),
            "causeType": d.get("causeType"),
            "deploymentId": d.get("deploymentId"),
            "deploymentVersion": d.get("deploymentVersion"),
            "databaseName": d.get("databaseName"),
        }
        for d in data
    ]
    return {
        "traceId": trace_id,
        "dependencyPath": ["gateway", "order", "payment", "inventory"],
        "timeline": timeline,
        "servicesInTrace": chain,
    }


def heuristic_analyze(data):
    errors = [d for d in data if d["level"] == "ERROR"]

    if not errors:
        return None, None, "No failure"

    prioritized = next(
        (d for d in reversed(errors) if d.get("causeType") in {"deployment", "database"}),
        errors[-1]
    )

    root = prioritized["service"]
    chain = list(dict.fromkeys(d["service"] for d in data))
    impacts = [svc for svc in chain if svc != root]
    cause_type = prioritized.get("causeType")
    evidence = []

    if cause_type == "deployment" and prioritized.get("deploymentId"):
        evidence.append(
            f"Recent deployment {prioritized['deploymentId']} (version {prioritized.get('deploymentVersion', 'unknown')})"
        )

    if cause_type == "database" and prioritized.get("databaseName"):
        evidence.append(f"Downstream database issue on {prioritized['databaseName']}")

    evidence.append(f"Error event: {prioritized.get('message', 'unknown error')}")

    text = f"""
Root Cause: {root}

Chain:
{" → ".join(chain)}

Impact:
{", ".join(impacts)}

Evidence:
{"; ".join(evidence)}
"""

    return root, chain, text


def llm_analyze(trace_id, data):
    if OpenAI is None or not os.getenv("OPENAI_API_KEY"):
        return None

    context = build_context(trace_id, data)
    client = OpenAI()
    prompt = f"""
You are an SRE root cause analysis assistant.

Given the incident context below, identify exactly one root cause service.
All other services should be treated as impacted services only.

Return valid JSON with this exact shape:
{{
  "rootCause": "service-name",
  "impactedServices": ["service-a", "service-b"],
  "reasoning": "short explanation"
}}

Rules:
- Pick exactly one root cause.
- Prefer the deepest failing service in the dependency path.
- Use deployment and database clues if present.
- Do not include markdown fences.

Incident context:
{json.dumps(context, indent=2)}
""".strip()

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=prompt,
        )
        content = json.loads(response.output_text)
        root = content["rootCause"]
        impacts = content.get("impactedServices", [])
        chain = [root] + [svc for svc in impacts if svc != root]
        text = f"""
Root Cause: {root}

Chain:
{" → ".join(chain)}

Impact:
{", ".join(impacts)}

Evidence:
{content.get("reasoning", "LLM-generated RCA")}
"""
        return root, chain, text
    except Exception as exc:
        print(f"⚠️ OpenAI RCA fallback: {exc}")
        return None


def analyze(trace_id, data):
    llm_result = llm_analyze(trace_id, data)
    if llm_result:
        return llm_result
    return heuristic_analyze(data)


def store(trace_id, root, chain, rca):
    query = """
    MERGE (i:Incident {traceId: $traceId})
    SET
        i.rca = $rca,
        i.rootCause = $root,
        i.updatedAt = timestamp()

    WITH i
    OPTIONAL MATCH (i)-[oldRoot:ROOT_CAUSE]->(:Service)
    DELETE oldRoot

    WITH i
    OPTIONAL MATCH (i)-[oldImpact:IMPACTS]->(:Service)
    DELETE oldImpact

    WITH i

    MATCH (s:Service {name: $root})
    MERGE (i)-[:ROOT_CAUSE]->(s)

    WITH i

    UNWIND $chain AS svc
    WITH i, svc WHERE svc <> $root
    MATCH (s:Service {name: svc})
    MERGE (i)-[:IMPACTS]->(s)
    """

    with driver.session() as session:
        session.run(query, {
            "traceId": trace_id,
            "root": root,
            "chain": chain,
            "rca": rca
        })


def run():
    traces = get_failed_traces()

    for t in traces:
        data = fetch_trace(t)
        root, chain, rca = analyze(t, data)

        print(f"\n🔥 TRACE: {t}")
        print("\n🔥 RCA RESULT:\n", rca)

        if root:
            store(t, root, chain, rca)


if __name__ == "__main__":
    run()
