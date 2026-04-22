from flask import Flask, request
from logger import get_logger
import requests
import random

app = Flask(__name__)
logger = get_logger("payment")


def get_trace_id():
    return request.headers.get("X-Trace-Id", "unknown")


@app.route("/")
def home():
    trace_id = get_trace_id()

    try:
        # 🔥 simulate random failure (demo purpose)
        if random.random() < 0.3:
            logger.custom_log("ERROR", "Inventory service failed", trace_id)
            return "Failure", 500

        res = requests.get(
            "http://inventory:5000",
            headers={"X-Trace-Id": trace_id}
        )

        if res.status_code != 200:
            logger.custom_log("ERROR", "Inventory failed", trace_id)
            return "Failure", 500

        logger.custom_log("INFO", "Payment processed", trace_id)
        return "Success"

    except Exception as e:
        logger.custom_log("ERROR", f"Inventory unreachable: {str(e)}", trace_id)
        return "Error", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)