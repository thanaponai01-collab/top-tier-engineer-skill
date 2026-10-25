"""`depot suppliers-newest`: newest the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} country={r['zone']} terms={r['tag']} qty={r['qty']}"


def _newest_suppliers(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("suppliers-newest")
def run(args):
    rows = store.load("suppliers")
    _newest_suppliers(rows, args)
