"""`depot waves-list`: list the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} planner={r['zone']} cutoff={r['tag']} qty={r['qty']}"


def _list_waves(rows, args):
    for r in rows:
        print(_line(r))


@command("waves-list")
def run(args):
    rows = store.load("waves")
    _list_waves(rows, args)
