"""Every run, appended to logs/runs.jsonl for later review."""
import json, os, time

LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "runs.jsonl")


def write(customer, message, history, outcome):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write(json.dumps({
            "ts": time.time(),
            "customer_email": customer["email"],
            "customer_address": customer["address"],
            "message": message,
            "history": history,
            "outcome": outcome,
        }) + "\n")
