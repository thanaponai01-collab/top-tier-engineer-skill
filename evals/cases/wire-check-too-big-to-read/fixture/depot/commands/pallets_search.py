"""`depot pallets-search`: search the pallets records (owner / rack)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} owner={r['zone']} rack={r['tag']} qty={r['qty']}"


def _search_pallets(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("pallets-search")
def run(args):
    rows = store.load("pallets")
    _search_pallets(rows, args)
