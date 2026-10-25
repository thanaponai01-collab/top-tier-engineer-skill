"""`depot routes-oldest`: oldest the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} driver={r['zone']} depot={r['tag']} qty={r['qty']}"


def _oldest_routes(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("routes-oldest")
def run(args):
    rows = store.load("routes")
    _oldest_routes(rows, args)
