"""Orders: what the web app reads and writes."""
from app.db import connect


def create_order(customer, total, status="paid"):
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO orders (customer, total, status, created_at) VALUES (?, ?, ?, datetime('now'))",
            (customer, total, status))
        return cur.lastrowid


def get_order(order_id):
    with connect() as conn:
        row = conn.execute("SELECT id, customer, total, status FROM orders WHERE id = ?", (order_id,)).fetchone()
    return dict(row) if row else None


def refund(order_id, amount):
    """Refund part of an order. Returns what is left to refund."""
    order = get_order(order_id)
    if order is None or order["status"] != "paid":
        raise ValueError("only paid orders can be refunded")
    left = order["total"] - amount
    if left < 0:
        raise ValueError("refund is more than the order")
    with connect() as conn:
        conn.execute("UPDATE orders SET total = ?, status = ? WHERE id = ?",
                     (left, "paid" if left else "refunded", order_id))
    return left


def order_line(order):
    return f"#{order['id']} {order['customer']}: ${order['total']:.2f}"
