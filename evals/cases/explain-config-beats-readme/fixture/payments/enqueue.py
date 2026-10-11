"""Called by checkout: put one charge on the queue."""
import uuid

from . import queue


def charge_later(order_id, amount_cents, card_token):
    queue.put({
        "order_id": order_id,
        "amount_cents": amount_cents,
        "card_token": card_token,
        # one key per charge, reused on every attempt: the gateway charges at most once per key
        "idempotency_key": str(uuid.uuid4()),
    })
