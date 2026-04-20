from neo4j import GraphDatabase
from openai import OpenAI
import os

# Optional: OpenAI client (fallback if fails)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Neo4j connection
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)


# =========================
# 🔍 FETCH GRAPH DATA
# =========================
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


# =========================
# 🧠 ANALYZE ROOT CAUSE
# =========================
def analyze_root_cause(data):

    # 🔥 Fallback logic (works without AI)
    def fallback():
        error_logs = [d for d in data if d["level"] == "ERROR"]

        if not error_logs:
            return None, None, "No failures detected"

        # sort oldest first
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

    # 🔥 Try OpenAI
    try:
        prompt = f"""
You are an expert SRE.

Analyze system logs and identify:
1. Root cause service
2. Failure chain
3. Impacted services
4. Suggested fix

Logs:
{data}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content

        # NOTE: AI parsing is optional → fallback used for structure
        root, chain, _ = fallback()

        return root, chain, text

    except Exception as e:
        print("⚠️ OpenAI failed, using fallback:", e)
        return fallback()


# =========================
# 💾 STORE INCIDENT RCA
# =========================
def store_incident(root, chain, rca_text):

    if not root or not chain:
        print("⚠️ Skipping incident storage")
        return

    query = """
    MERGE (i:Incident {service: $root, status: "OPEN"})
    ON CREATE SET
        i.id = randomUUID(),
        i.createdAt = timestamp(),
        i.severity = "CRITICAL"

    SET i.rca = $rca

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
            "root": root,
            "chain": chain,
            "rca": rca_text
        })

    print(f"🔥 Incident updated with RCA: root={root}")


# =========================
# 🚀 MAIN RUNNER
# =========================
def run():
    print("🚀 Running RCA Agent...")

    data = fetch_graph_data()

    if not data:
        print("❌ No data found")
        return

    # Skip if no errors
    if not any(d["level"] == "ERROR" for d in data):
        print("✅ No errors — skipping RCA")
        return

    root, chain, result = analyze_root_cause(data)

    print("\n🤖 RCA RESULT:\n")
    print(result)

    # Store in Neo4j
    store_incident(root, chain, result)


if __name__ == "__main__":
    run()