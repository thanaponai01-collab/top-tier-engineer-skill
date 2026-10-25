"""Customer receipts: one message per paid order, for the mailer daemon to send."""
from store import outbox


def build(order):
    return {
        "to": order["customer"],
        "subject": f"Receipt for order {order['id']}",
        "body": f"Thanks! We received {order['amount']:.2f}.",
    }


def send(order):
    outbox.enqueue(build(order))
