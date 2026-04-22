import json
import logging
import sys
import time
from elasticsearch import Elasticsearch


# ===============================
# CONNECT TO ELASTICSEARCH
# ===============================
def get_es():
    for _ in range(20):
        try:
            print("🔍 Trying to connect to Elasticsearch...")

            es = Elasticsearch(
                "http://elasticsearch:9200",
                verify_certs=False,
                request_timeout=30
            )

            es.info()  # check connection

            print("✅ Connected to Elasticsearch")
            return es

        except Exception as e:
            print("Retrying ES...", e)

        time.sleep(5)

    print("❌ Failed to connect to Elasticsearch")
    return None


# ===============================
# LOGGER SETUP
# ===============================
def get_logger(service_name):
    print(f"🔥 LOGGER LOADED → {service_name}")

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)

    try:
        es = get_es()
    except Exception as e:
        print("Logger init failed:", e)
        es = None


    # ===============================
    # CUSTOM LOG FUNCTION
    # ===============================
    def log(level, message, trace_id=None):
        log_entry = {
            "service": service_name,
            "level": level,
            "message": message,
            "traceId": trace_id if trace_id else "unknown",
            "timestamp": time.time()
        }

        # Print log
        logger.info(json.dumps(log_entry))

        # Push to Elasticsearch
        if es:
            try:
                es.index(
                    index="logs",
                    document=log_entry
                )
            except Exception as e:
                print("❌ Elasticsearch error:", e)

    # attach custom function
    logger.custom_log = log

    return logger