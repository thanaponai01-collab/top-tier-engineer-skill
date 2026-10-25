"""`depot routes-top`: top the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} driver={r['zone']} depot={r['tag']} qty={r['qty']}"


def _top_routes(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("routes-top")
def run(args):
    rows = store.load("routes")
    _top_routes(rows, args)
