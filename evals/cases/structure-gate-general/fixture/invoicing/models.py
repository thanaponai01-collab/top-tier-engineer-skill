"""Orders and customers as plain dicts, loaded through the store."""
from invoicing import store


def load_order(order_id):
    raw = store.get("orders", order_id)
    raw.setdefault("lines", [])
    return raw


def load_customer(customer_id):
    raw = store.get("customers", customer_id)
    raw.setdefault("orders", 0)
    return raw


def blank_order():
    return {"lines": [], "coupon": None, "ship": True, "express": False}
