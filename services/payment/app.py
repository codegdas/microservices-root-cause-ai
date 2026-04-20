from flask import Flask
from logger import get_logger
import requests
import random

app = Flask(__name__)
logger = get_logger("payment")

@app.route("/")
def payment():
    if random.random() < 0.3:
        logger.custom_log("ERROR", "Inventory service failed")
        return "Failure", 500

    try:
        res = requests.get("http://inventory:5000")

        if res.status_code != 200:
            logger.custom_log("ERROR", "Inventory failed")
            return "Failure", 500

        logger.custom_log("INFO", "Payment processed")
        return "Success"

    except Exception as e:
        logger.custom_log("ERROR", f"Inventory unreachable: {str(e)}")
        return "Error", 500

app.run(host="0.0.0.0", port=5000)