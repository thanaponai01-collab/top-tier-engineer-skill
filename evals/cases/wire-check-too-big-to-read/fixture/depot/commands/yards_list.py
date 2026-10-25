"""`depot yards-list`: list the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} gate={r['zone']} spot={r['tag']} qty={r['qty']}"


def _list_yards(rows, args):
    for r in rows:
        print(_line(r))


@command("yards-list")
def run(args):
    rows = store.load("yards")
    _list_yards(rows, args)
