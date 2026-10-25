"""`depot waves-oldest`: oldest the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} planner={r['zone']} cutoff={r['tag']} qty={r['qty']}"


def _oldest_waves(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("waves-oldest")
def run(args):
    rows = store.load("waves")
    _oldest_waves(rows, args)
