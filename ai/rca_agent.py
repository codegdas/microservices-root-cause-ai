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
    RETURN s.name AS service, e.level AS level, e.timestamp AS ts
    ORDER BY ts ASC
    """

    with driver.session() as session:
        return [dict(r) for r in session.run(query, {"traceId": trace_id})]


def analyze(data):
    errors = [d for d in data if d["level"] == "ERROR"]

    if not errors:
        return None, None, "No failure"

    root = errors[-1]["service"]
    chain = [d["service"] for d in data]

    text = f"""
Root Cause: {root}

Chain:
{" → ".join(chain)}

Impact:
{", ".join(set(chain) - {root})}
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

    MATCH (s:Service {name: $root})
    MERGE (i)-[:ROOT_CAUSE]->(s)

    WITH i

    UNWIND $chain AS svc
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
