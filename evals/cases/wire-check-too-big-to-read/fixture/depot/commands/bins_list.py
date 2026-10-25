"""`depot bins-list`: list the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} zone={r['zone']} aisle={r['tag']} qty={r['qty']}"


def _list_bins(rows, args):
    for r in rows:
        print(_line(r))


@command("bins-list")
def run(args):
    rows = store.load("bins")
    _list_bins(rows, args)
