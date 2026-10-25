"""`depot cycle-oldest`: oldest the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} counter={r['zone']} shift={r['tag']} qty={r['qty']}"


def _oldest_cycle(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("cycle-oldest")
def run(args):
    rows = store.load("cycle")
    _oldest_cycle(rows, args)
