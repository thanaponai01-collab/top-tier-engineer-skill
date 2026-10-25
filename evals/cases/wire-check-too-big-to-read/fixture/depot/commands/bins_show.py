"""`depot bins-show`: show the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} zone={r['zone']} aisle={r['tag']} qty={r['qty']}"


def _show_bins(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("bins-show")
def run(args):
    rows = store.load("bins")
    _show_bins(rows, args)
