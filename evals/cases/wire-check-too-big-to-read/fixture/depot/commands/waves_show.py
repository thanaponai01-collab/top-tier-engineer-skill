"""`depot waves-show`: show the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} planner={r['zone']} cutoff={r['tag']} qty={r['qty']}"


def _show_waves(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("waves-show")
def run(args):
    rows = store.load("waves")
    _show_waves(rows, args)
