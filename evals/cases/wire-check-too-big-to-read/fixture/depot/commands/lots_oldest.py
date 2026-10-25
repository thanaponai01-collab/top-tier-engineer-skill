"""`depot lots-oldest`: oldest the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} batch={r['zone']} expiry={r['tag']} qty={r['qty']}"


def _oldest_lots(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("lots-oldest")
def run(args):
    rows = store.load("lots")
    _oldest_lots(rows, args)
