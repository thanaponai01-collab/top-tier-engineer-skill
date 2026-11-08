import json
import os

from .models import Order

PATH = os.path.join("data", "orders.json")


def load(path=PATH):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [Order.from_dict(d) for d in json.load(fh)]


def save(orders, path=PATH):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([o.to_dict() for o in orders], fh, indent=2)
