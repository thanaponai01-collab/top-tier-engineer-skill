"""`depot pallets-top`: top the pallets records (owner / rack)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} owner={r['zone']} rack={r['tag']} qty={r['qty']}"


def _top_pallets(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("pallets-top")
def run(args):
    rows = store.load("pallets")
    _top_pallets(rows, args)
