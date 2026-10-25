"""`depot pallets-list`: list the pallets records (owner / rack)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} owner={r['zone']} rack={r['tag']} qty={r['qty']}"


def _list_pallets(rows, args):
    for r in rows:
        print(_line(r))


@command("pallets-list")
def run(args):
    rows = store.load("pallets")
    _list_pallets(rows, args)
