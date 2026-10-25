"""`depot totes-oldest`: oldest the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} color={r['zone']} lane={r['tag']} qty={r['qty']}"


def _oldest_totes(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("totes-oldest")
def run(args):
    rows = store.load("totes")
    _oldest_totes(rows, args)
