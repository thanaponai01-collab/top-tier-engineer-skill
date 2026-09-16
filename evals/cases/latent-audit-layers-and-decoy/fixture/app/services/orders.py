"""Domain layer."""
from app.models.order import save


def place_order(items):
    total = sum(i["price"] for i in items)
    return save(total)
