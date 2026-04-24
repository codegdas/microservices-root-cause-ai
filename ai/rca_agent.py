# rca_agent.py

from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)


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


def analyze(data):
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
        root, chain, rca = analyze(data)

        print("\n🔥 RCA RESULT:\n", rca)

        if root:
            store(t, root, chain, rca)


if __name__ == "__main__":
    run()
