import time
from ingestion.es_to_neo4j import run as ingest
from ai.rca_agent import run as rca

def pipeline():
    print("\n🔄 Running pipeline cycle...")

    # Step 1: Ingest logs → Neo4j
    ingest()

    # Step 2: Run AI RCA
    print("🧠 Running RCA...")
    rca()

    print("✅ Cycle complete\n")


if __name__ == "__main__":
    while True:
        pipeline()
        time.sleep(10)  # run every 10 sec