from flask import Flask, request
from logger import get_logger
import requests
import random
import os
import time

app = Flask(__name__)
logger = get_logger("payment")
PAYMENT_VERSION = os.getenv("PAYMENT_VERSION", "2.3.1")
DEPLOYED_AT = float(os.getenv("PAYMENT_DEPLOYED_AT", str(time.time())))
PAYMENT_DATABASE = os.getenv("PAYMENT_DATABASE", "payments-db")


def get_trace_id():
    return request.headers.get("X-Trace-Id", "unknown")


@app.route("/")
def home():
    trace_id = get_trace_id()

    try:
        failure_roll = random.random()

        if failure_roll < 0.15:
            logger.custom_log(
                "ERROR",
                "Payment failed after recent deployment",
                trace_id,
                causeType="deployment",
                deploymentId=f"payment-{PAYMENT_VERSION}",
                deploymentVersion=PAYMENT_VERSION,
                deployedAt=DEPLOYED_AT
            )
            return "Failure", 500

        if failure_roll < 0.30:
            logger.custom_log(
                "ERROR",
                "Payment database connection timeout",
                trace_id,
                causeType="database",
                databaseName=PAYMENT_DATABASE,
                dependencyType="postgres"
            )
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
