"""`depot totes-top`: top the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} color={r['zone']} lane={r['tag']} qty={r['qty']}"


def _top_totes(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("totes-top")
def run(args):
    rows = store.load("totes")
    _top_totes(rows, args)
