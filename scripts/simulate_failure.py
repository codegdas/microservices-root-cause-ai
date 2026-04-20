import requests
import time
import random

GATEWAY_URL = "http://localhost:5001"

def simulate():
    while True:
        try:
            print("🚀 Sending request to gateway...")

            res = requests.get(GATEWAY_URL)

            if res.status_code == 200:
                print("✅ Success")
            else:
                print("❌ Failure detected")

        except Exception as e:
            print("🔥 Error:", e)

        # random delay (simulate real traffic)
        time.sleep(random.uniform(1, 3))


if __name__ == "__main__":
    simulate()