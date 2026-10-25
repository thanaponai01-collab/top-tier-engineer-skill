"""`depot waves-newest`: newest the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} planner={r['zone']} cutoff={r['tag']} qty={r['qty']}"


def _newest_waves(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("waves-newest")
def run(args):
    rows = store.load("waves")
    _newest_waves(rows, args)
