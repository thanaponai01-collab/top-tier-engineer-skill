"""`depot routes-show`: show the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} driver={r['zone']} depot={r['tag']} qty={r['qty']}"


def _show_routes(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("routes-show")
def run(args):
    rows = store.load("routes")
    _show_routes(rows, args)
