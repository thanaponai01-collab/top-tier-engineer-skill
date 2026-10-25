"""`depot suppliers-oldest`: oldest the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} country={r['zone']} terms={r['tag']} qty={r['qty']}"


def _oldest_suppliers(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("suppliers-oldest")
def run(args):
    rows = store.load("suppliers")
    _oldest_suppliers(rows, args)
