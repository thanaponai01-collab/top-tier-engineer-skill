"""Data layer — but it reaches up into the interface layer for its copy."""
from app.routes.web import BANNER


def subject(order_id):
    return f"{BANNER} #{order_id}"
