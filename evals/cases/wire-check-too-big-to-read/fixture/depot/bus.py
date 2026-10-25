"""In-process events: handlers subscribe by name, commands publish."""
_subscribers = {}


def subscribe(event):
    def register(fn):
        _subscribers.setdefault(event, []).append(fn)
        return fn
    return register


def publish(event, **payload):
    for fn in _subscribers.get(event, []):
        fn(**payload)
