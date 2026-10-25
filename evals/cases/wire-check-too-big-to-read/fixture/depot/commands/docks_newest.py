"""`depot docks-newest`: newest the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} yard={r['zone']} slot={r['tag']} qty={r['qty']}"


def _newest_docks(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("docks-newest")
def run(args):
    rows = store.load("docks")
    _newest_docks(rows, args)
