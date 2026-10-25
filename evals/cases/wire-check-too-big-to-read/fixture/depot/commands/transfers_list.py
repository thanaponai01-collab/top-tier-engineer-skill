"""`depot transfers-list`: list the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} origin={r['zone']} dest={r['tag']} qty={r['qty']}"


def _list_transfers(rows, args):
    for r in rows:
        print(_line(r))


@command("transfers-list")
def run(args):
    rows = store.load("transfers")
    _list_transfers(rows, args)
