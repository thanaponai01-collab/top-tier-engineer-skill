"""Refunds are recorded as a negative line on the order, so the history stays intact."""
from money import fmt
from orders.model import Line


def refund(order, line_id):
    original = order.line(line_id)
    credit = Line(id=f"{line_id}-R", sku=original.sku, price_cents=-original.price_cents,
                  qty=original.qty)
    order.lines.append(credit)
    order.status = "refunded" if order.total <= 0 else "partly refunded"
    return (f"Refunded {original.sku} x{original.qty} ({fmt(-credit.subtotal())}) on {order.id}. "
            f"New total {fmt(order.total)}.")
