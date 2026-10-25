"""`depot transfers-oldest`: oldest the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} origin={r['zone']} dest={r['tag']} qty={r['qty']}"


def _oldest_transfers(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("transfers-oldest")
def run(args):
    rows = store.load("transfers")
    _oldest_transfers(rows, args)
