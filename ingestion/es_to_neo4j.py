from elasticsearch import Elasticsearch
from neo4j import GraphDatabase
from ingestion.log_to_graph import transform_log

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Connect to Neo4j
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

def test_neo4j():
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            print("✅ Neo4j connected:", result.single()["test"])
    except Exception as e:
        print("❌ Neo4j connection failed:", e)


def fetch_logs():
    try:
        res = es.search(
            index="logs",
            query={"match_all": {}},   # 🔥 important fix
            size=50
        )

        logs = [hit["_source"] for hit in res["hits"]["hits"]]

        print(f"📦 Logs fetched: {len(logs)}")

        return logs

    except Exception as e:
        print("❌ Error fetching logs from ES:", e)
        return []


def write_to_neo4j(log):
    try:
        query, params = transform_log(log)

        with driver.session() as session:
            session.run(query, params)

        print("➡️ Written to Neo4j:", log)

    except Exception as e:
        print("❌ Error writing to Neo4j:", e)


def run():
    print("🚀 Starting ingestion pipeline...")

    test_neo4j()  # 🔥 check Neo4j first

    logs = fetch_logs()

    if not logs:
        print("❌ No logs found in Elasticsearch")
        return

    for log in logs:
        write_to_neo4j(log)

    print("✅ Data written to Neo4j")


if __name__ == "__main__":
    run()