"""`depot waves-top`: top the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} planner={r['zone']} cutoff={r['tag']} qty={r['qty']}"


def _top_waves(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("waves-top")
def run(args):
    rows = store.load("waves")
    _top_waves(rows, args)
