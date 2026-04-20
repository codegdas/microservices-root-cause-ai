from flask import Flask
from logger import get_logger
import requests
import random

app = Flask(__name__)
logger = get_logger("gateway")

@app.route("/")
def home():
    try:
        # Call order service
        res = requests.get("http://order:5000")

        if res.status_code != 200:
            logger.custom_log("ERROR", "Order service failed")
            return "Failure", 500

        logger.custom_log("INFO", "Gateway request successful")
        return "Success"

    except Exception as e:
        logger.custom_log("ERROR", f"Order service unreachable: {str(e)}")
        return "Error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)