"""v1 export: CSV only. Deprecated in favour of /v2/export."""
from .data import ORDERS


def handle(params):
    lines = ["id,customer,total"] + [f"{o['id']},{o['customer']},{o['total']}" for o in ORDERS]
    return "\n".join(lines)
