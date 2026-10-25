"""Routes contributed by integrations (settings.INTEGRATIONS); app.py merges them into ROUTES."""
EXTRA = {}


def route(method, path):
    def register(fn):
        EXTRA[(method, path)] = fn
        return fn
    return register
