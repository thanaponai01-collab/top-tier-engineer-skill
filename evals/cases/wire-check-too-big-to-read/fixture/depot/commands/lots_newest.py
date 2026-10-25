"""`depot lots-newest`: newest the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} batch={r['zone']} expiry={r['tag']} qty={r['qty']}"


def _newest_lots(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("lots-newest")
def run(args):
    rows = store.load("lots")
    _newest_lots(rows, args)
