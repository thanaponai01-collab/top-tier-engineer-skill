"""`depot suppliers-search`: search the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} country={r['zone']} terms={r['tag']} qty={r['qty']}"


def _search_suppliers(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("suppliers-search")
def run(args):
    rows = store.load("suppliers")
    _search_suppliers(rows, args)
