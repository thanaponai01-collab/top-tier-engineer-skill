"""Outgoing webhooks: each event is delivered with retries, then given up on."""
MAX_ATTEMPTS = 5


class Delivery:
    def __init__(self, url, event):
        self.url = url
        self.event = event
        self.status = "queued"
        self.attempts = 0
        self.last_code = None


def attempt(delivery, send):
    if delivery.status not in ("queued", "failed"):
        return delivery.status
    delivery.attempts += 1
    code = send(delivery.url, delivery.event)
    delivery.last_code = code
    if 200 <= code < 300:
        delivery.status = "sent"
    elif delivery.attempts >= MAX_ATTEMPTS:
        delivery.status = "dead"
    else:
        delivery.status = "failed"
    return delivery.status


def retry_due(deliveries):
    return [d for d in deliveries if d.status == "failed"]
