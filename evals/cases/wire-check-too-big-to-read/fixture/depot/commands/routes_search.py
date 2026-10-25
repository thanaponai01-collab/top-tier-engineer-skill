"""`depot routes-search`: search the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} driver={r['zone']} depot={r['tag']} qty={r['qty']}"


def _search_routes(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("routes-search")
def run(args):
    rows = store.load("routes")
    _search_routes(rows, args)
