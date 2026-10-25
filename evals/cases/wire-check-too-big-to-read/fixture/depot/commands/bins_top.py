"""`depot bins-top`: top the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} zone={r['zone']} aisle={r['tag']} qty={r['qty']}"


def _top_bins(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("bins-top")
def run(args):
    rows = store.load("bins")
    _top_bins(rows, args)
