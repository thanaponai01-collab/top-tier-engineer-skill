"""`depot suppliers-top`: top the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} country={r['zone']} terms={r['tag']} qty={r['qty']}"


def _top_suppliers(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("suppliers-top")
def run(args):
    rows = store.load("suppliers")
    _top_suppliers(rows, args)
