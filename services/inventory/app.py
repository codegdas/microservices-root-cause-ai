from flask import Flask
from logger import get_logger

app = Flask(__name__)
logger = get_logger("inventory")

@app.route("/")
def inventory():
    logger.custom_log("INFO", "Inventory checked")
    return "Success"

app.run(host="0.0.0.0", port=5000)