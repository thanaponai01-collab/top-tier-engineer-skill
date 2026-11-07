import http.client
import json
import time

HOST = "pay.example.invalid"


def charge(order_id, cents):
    body = json.dumps({"order": order_id, "amount": cents})
    for attempt in range(4):
        conn = http.client.HTTPSConnection(HOST, timeout=15)
        try:
            conn.request("POST", "/charge", body, {"Content-Type": "application/json"})
            resp = conn.getresponse()
            if resp.status in (502, 503):
                time.sleep(1 + attempt)
                continue
            return resp.status == 201
        except OSError:
            time.sleep(1 + attempt)
        finally:
            conn.close()
    return False
