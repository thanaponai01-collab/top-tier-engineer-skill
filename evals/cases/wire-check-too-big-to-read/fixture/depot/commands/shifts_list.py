"""`depot shifts-list`: list the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} lead={r['zone']} site={r['tag']} qty={r['qty']}"


def _list_shifts(rows, args):
    for r in rows:
        print(_line(r))


@command("shifts-list")
def run(args):
    rows = store.load("shifts")
    _list_shifts(rows, args)
