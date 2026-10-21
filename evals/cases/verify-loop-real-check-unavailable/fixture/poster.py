"""Post refunds to the ledger."""
import json
import subprocess


def build_payload(order_id, amount):
    """The ledger entry for refunding `amount` dollars on `order_id`."""
    return {"type": "refund", "order": order_id, "amount_cents": -round(amount * 100)}


def post_refund(order_id, amount, run=subprocess.run):
    """Post the refund; return what the ledger printed."""
    payload = json.dumps(build_payload(order_id, amount))
    out = run(["ledgerctl", "post", "--json", payload], capture_output=True, text=True, check=True)
    return out.stdout.strip()
