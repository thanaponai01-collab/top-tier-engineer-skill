"""`depot lots-list`: list the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} batch={r['zone']} expiry={r['tag']} qty={r['qty']}"


def _list_lots(rows, args):
    for r in rows:
        print(_line(r))


@command("lots-list")
def run(args):
    rows = store.load("lots")
    _list_lots(rows, args)
