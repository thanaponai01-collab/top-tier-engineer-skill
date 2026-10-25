"""`depot cycle-top`: top the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} counter={r['zone']} shift={r['tag']} qty={r['qty']}"


def _top_cycle(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("cycle-top")
def run(args):
    rows = store.load("cycle")
    _top_cycle(rows, args)
