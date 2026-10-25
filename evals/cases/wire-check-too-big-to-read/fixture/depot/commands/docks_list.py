"""`depot docks-list`: list the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} yard={r['zone']} slot={r['tag']} qty={r['qty']}"


def _list_docks(rows, args):
    for r in rows:
        print(_line(r))


@command("docks-list")
def run(args):
    rows = store.load("docks")
    _list_docks(rows, args)
