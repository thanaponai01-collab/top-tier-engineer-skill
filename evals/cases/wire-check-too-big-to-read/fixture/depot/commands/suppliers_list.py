"""`depot suppliers-list`: list the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} country={r['zone']} terms={r['tag']} qty={r['qty']}"


def _list_suppliers(rows, args):
    for r in rows:
        print(_line(r))


@command("suppliers-list")
def run(args):
    rows = store.load("suppliers")
    _list_suppliers(rows, args)
