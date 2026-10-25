"""`depot bins-oldest`: oldest the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} zone={r['zone']} aisle={r['tag']} qty={r['qty']}"


def _oldest_bins(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("bins-oldest")
def run(args):
    rows = store.load("bins")
    _oldest_bins(rows, args)
