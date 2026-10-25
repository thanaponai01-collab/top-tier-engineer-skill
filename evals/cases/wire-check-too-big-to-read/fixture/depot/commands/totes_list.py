"""`depot totes-list`: list the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} color={r['zone']} lane={r['tag']} qty={r['qty']}"


def _list_totes(rows, args):
    for r in rows:
        print(_line(r))


@command("totes-list")
def run(args):
    rows = store.load("totes")
    _list_totes(rows, args)
