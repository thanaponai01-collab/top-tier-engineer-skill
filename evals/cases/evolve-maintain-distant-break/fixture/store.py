import json
import os

from orders.model import Order

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "orders.json")


def load_orders(path=DATA):
    with open(path, encoding="utf-8") as f:
        return [Order.from_dict(d) for d in json.load(f)]


def save_orders(orders, path=DATA):
    with open(path, "w", encoding="utf-8") as f:
        json.dump([o.to_dict() for o in orders], f, indent=2)
        f.write("\n")


def find(orders, order_id):
    for o in orders:
        if o.id == order_id:
            return o
    raise SystemExit(f"no order {order_id}")
