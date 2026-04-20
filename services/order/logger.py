import json
import logging
import sys
import time
from elasticsearch import Elasticsearch

def get_es():
    for _ in range(20):
        try:
            print("🔍 Trying to connect to Elasticsearch...")

            es = Elasticsearch(
                "http://elasticsearch:9200",
                verify_certs=False,
                request_timeout=30
            )

            # 🔥 Use info() instead of ping()
            es.info()

            print("✅ Connected to Elasticsearch")
            return es

        except Exception as e:
            print("Retrying ES...", e)

        time.sleep(5)

    print("❌ Failed to connect to Elasticsearch")
    return None

def get_logger(service_name):
    print("🔥 LOGGER LOADED")

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

    try:
        es = get_es()
    except Exception as e:
        print("Logger init failed:", e)
        es = None

    def log(level, message):
        log_entry = {
            "service": service_name,
            "level": level,
            "message": message,
            "timestamp": time.time()
        }

        logger.info(json.dumps(log_entry))

        if es:
            try:
                es.index(index="logs", document=log_entry)
            except Exception as e:
                print("Elasticsearch error:", e)

    logger.custom_log = log
    return logger