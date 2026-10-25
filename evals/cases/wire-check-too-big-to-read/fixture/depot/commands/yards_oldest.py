"""`depot yards-oldest`: oldest the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} gate={r['zone']} spot={r['tag']} qty={r['qty']}"


def _oldest_yards(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("yards-oldest")
def run(args):
    rows = store.load("yards")
    _oldest_yards(rows, args)
