"""`depot transfers-newest`: newest the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} origin={r['zone']} dest={r['tag']} qty={r['qty']}"


def _newest_transfers(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("transfers-newest")
def run(args):
    rows = store.load("transfers")
    _newest_transfers(rows, args)
