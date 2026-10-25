"""`depot bins-search`: search the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} zone={r['zone']} aisle={r['tag']} qty={r['qty']}"


def _search_bins(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("bins-search")
def run(args):
    rows = store.load("bins")
    _search_bins(rows, args)
