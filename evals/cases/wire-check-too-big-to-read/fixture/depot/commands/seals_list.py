"""`depot seals-list`: list the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} trailer={r['zone']} inspector={r['tag']} qty={r['qty']}"


def _list_seals(rows, args):
    for r in rows:
        print(_line(r))


@command("seals-list")
def run(args):
    rows = store.load("seals")
    _list_seals(rows, args)
