"""`depot yards-top`: top the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} gate={r['zone']} spot={r['tag']} qty={r['qty']}"


def _top_yards(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("yards-top")
def run(args):
    rows = store.load("yards")
    _top_yards(rows, args)
