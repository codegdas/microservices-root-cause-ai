import requests
import time
import random
import uuid

GATEWAY_URL = "http://localhost:5001"

def simulate():
    while True:
        try:
            # 🔥 Create ONE traceId per request flow
            trace_id = str(uuid.uuid4())

            print(f"\n🚀 Sending request | traceId={trace_id}")

            # 👇 Send traceId as header
            res = requests.get(
                GATEWAY_URL,
                headers={"X-Trace-Id": trace_id}
            )

            if res.status_code == 200:
                print("✅ Success")
            else:
                print("❌ Failure detected")

        except Exception as e:
            print("🔥 Error:", e)

        # random delay
        time.sleep(random.uniform(1, 3))


if __name__ == "__main__":
    simulate()