"""`depot yards-newest`: newest the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} gate={r['zone']} spot={r['tag']} qty={r['qty']}"


def _newest_yards(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("yards-newest")
def run(args):
    rows = store.load("yards")
    _newest_yards(rows, args)
