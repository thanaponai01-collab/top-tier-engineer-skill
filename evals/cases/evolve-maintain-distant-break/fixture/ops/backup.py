"""Backups dump every attribute of every object (default=vars), so a field added to the model
later is never silently left out of a backup."""
import json

from money import fmt
from orders.model import Order


def backup(orders, path):
    worth = sum(o.total for o in orders)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(orders, f, default=vars, indent=2)
    return f"Backed up {len(orders)} orders worth {fmt(worth)} to {path}"


def restore(path):
    with open(path, encoding="utf-8") as f:
        return [Order.from_dict(d) for d in json.load(f)]
