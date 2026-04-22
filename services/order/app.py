from flask import Flask, request
from logger import get_logger
import requests

app = Flask(__name__)
logger = get_logger("order")


def get_trace_id():
    return request.headers.get("X-Trace-Id", "unknown")


@app.route("/")
def home():
    trace_id = get_trace_id()

    try:
        res = requests.get(
            "http://payment:5000",
            headers={"X-Trace-Id": trace_id}
        )

        if res.status_code != 200:
            logger.custom_log("ERROR", "Payment failed", trace_id)
            return "Failure", 500

        logger.custom_log("INFO", "Order processed", trace_id)
        return "Success"

    except Exception as e:
        logger.custom_log("ERROR", f"Payment unreachable: {str(e)}", trace_id)
        return "Error", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)