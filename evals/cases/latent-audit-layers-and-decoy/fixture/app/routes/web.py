"""Interface layer."""
from app.services.orders import place_order

BANNER = "orders"


def handle(payload):
    return place_order(payload["items"])
