from app.legacy_sync import push


def run(items):
    return f"pushed: {push(items)}"
