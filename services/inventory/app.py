from flask import Flask, request
from logger import get_logger

app = Flask(__name__)
logger = get_logger("inventory")


def get_trace_id():
    return request.headers.get("X-Trace-Id", "unknown")


@app.route("/")
def home():
    trace_id = get_trace_id()

    # always success (you can also simulate failure here if needed)
    logger.custom_log("INFO", "Inventory checked", trace_id)
    return "Success"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)