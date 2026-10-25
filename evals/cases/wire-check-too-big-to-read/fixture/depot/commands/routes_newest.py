"""`depot routes-newest`: newest the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} driver={r['zone']} depot={r['tag']} qty={r['qty']}"


def _newest_routes(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("routes-newest")
def run(args):
    rows = store.load("routes")
    _newest_routes(rows, args)
