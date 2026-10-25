"""`depot pallets-oldest`: oldest the pallets records (owner / rack)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} owner={r['zone']} rack={r['tag']} qty={r['qty']}"


def _oldest_pallets(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("pallets-oldest")
def run(args):
    rows = store.load("pallets")
    _oldest_pallets(rows, args)
