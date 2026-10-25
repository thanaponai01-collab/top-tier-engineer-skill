"""In-process event bus: handlers subscribe by event name, inventory publishes."""
_subscribers = {}


def subscribe(event):
    def register(fn):
        _subscribers.setdefault(event, []).append(fn)
        return fn
    return register


def publish(event, **payload):
    for fn in _subscribers.get(event, []):
        try:
            fn(**payload)
        except Exception:
            # A broken side effect must never fail a sale.
            pass
