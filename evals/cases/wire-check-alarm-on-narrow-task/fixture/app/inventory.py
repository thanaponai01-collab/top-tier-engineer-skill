import json

from app import bus
from app.config import INVENTORY_FILE


def load():
    with open(INVENTORY_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def save(stock):
    with open(INVENTORY_FILE, "w", encoding="utf-8") as fh:
        json.dump(stock, fh)


def change(sku, delta):
    stock = load()
    before = stock.get(sku, 0)
    after = before + delta
    if after < 0:
        raise SystemExit(f"only {before} {sku} on hand")
    stock[sku] = after
    save(stock)
    bus.publish("stock.changed", sku=sku, qty=after, before=before)
    return after
