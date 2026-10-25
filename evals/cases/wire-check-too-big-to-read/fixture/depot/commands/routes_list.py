"""`depot routes-list`: list the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} driver={r['zone']} depot={r['tag']} qty={r['qty']}"


def _list_routes(rows, args):
    for r in rows:
        print(_line(r))


@command("routes-list")
def run(args):
    rows = store.load("routes")
    _list_routes(rows, args)
