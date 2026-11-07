import json
import time
import urllib.request

WEBHOOK = "https://hooks.example.invalid/orders"


def send_order_email(order_id, email):
    body = json.dumps({"order": order_id, "to": email}).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(WEBHOOK, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except OSError:
            time.sleep(2 ** attempt)
    return False
