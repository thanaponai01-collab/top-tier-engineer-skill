"""`depot cycle-list`: list the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} counter={r['zone']} shift={r['tag']} qty={r['qty']}"


def _list_cycle(rows, args):
    for r in rows:
        print(_line(r))


@command("cycle-list")
def run(args):
    rows = store.load("cycle")
    _list_cycle(rows, args)
