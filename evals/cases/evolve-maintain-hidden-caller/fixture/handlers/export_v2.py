"""v2 export: CSV or JSON (fmt=csv|json, default json)."""
import json

from .data import ORDERS


def handle(params):
    if params.get("fmt", "json") == "csv":
        lines = ["id,customer,total"] + [f"{o['id']},{o['customer']},{o['total']}" for o in ORDERS]
        return "\n".join(lines)
    return json.dumps(ORDERS)
