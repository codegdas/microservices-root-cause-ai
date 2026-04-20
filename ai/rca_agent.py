from neo4j import GraphDatabase
from openai import OpenAI

# OpenAI client (optional – fallback if fails)
client = OpenAI()

# Neo4j connection
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)


# 🔍 Fetch data
def fetch_graph_data():
    query = """
    MATCH (s:Service)-[:GENERATED]->(e:Event)
    RETURN s.name AS service, e.level AS level, e.message AS message, e.timestamp AS timestamp
    ORDER BY e.timestamp DESC
    LIMIT 50
    """

    with driver.session() as session:
        result = session.run(query)
        data = [dict(r) for r in result]

    print(f"📊 Fetched {len(data)} events from graph")
    return data


# 🧠 RCA logic
def analyze_root_cause(data):

    def fallback():
        error_logs = [d for d in data if d["level"] == "ERROR"]

        if not error_logs:
            return None, None, "No failures detected"

        error_logs_sorted = sorted(error_logs, key=lambda x: x["timestamp"])

        services = []
        for log in error_logs_sorted:
            if log["service"] not in services:
                services.append(log["service"])

        root = services[0]
        chain = services[::-1]

        result_text = f"""
Root Cause: {root}

Failure Chain:
{" → ".join(chain)}

Impacted Services:
{", ".join(services[1:])}
"""

        return root, chain, result_text

    try:
        prompt = f"""
Analyze logs and find:
1. Root cause
2. Failure chain
3. Impact

Logs:
{data}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content
        return None, None, text

    except Exception as e:
        print("⚠️ OpenAI failed, using fallback:", e)
        return fallback()


# 💾 Store Incident
def store_incident(root, chain, rca_text):

    if not root or not chain:
        print("⚠️ Skipping incident storage")
        return

    query = """
    CREATE (i:Incident {
        uuid: randomUUID(),
        rootCause: $root,
        failureChain: $chain,
        rca: $rca,
        severity: "HIGH",
        createdAt: timestamp(),
        createdBy: "rca-agent"
    })
    WITH i

    MATCH (s:Service {name: $root})
    MERGE (i)-[:ROOT_CAUSE]->(s)

    WITH i
    UNWIND $chain AS svc
    MATCH (s:Service {name: svc})
    MERGE (i)-[:IMPACTED]->(s)
    """

    with driver.session() as session:
        session.run(query, {
            "root": root,
            "chain": " → ".join(chain),
            "rca": rca_text
        })

    print(f"🔥 Incident stored with RCA: root={root}")


# 🚀 Runner
def run():
    print("🚀 Running RCA Agent...")

    data = fetch_graph_data()

    if not data:
        print("❌ No data found")
        return

    if not any(d["level"] == "ERROR" for d in data):
        print("✅ No errors — skipping RCA")
        return

    root, chain, result = analyze_root_cause(data)

    print("\n🤖 RCA RESULT:\n")
    print(result)

    # ✅ FIXED
    store_incident(root, chain, result)


if __name__ == "__main__":
    run()