"""`depot docks-top`: top the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} yard={r['zone']} slot={r['tag']} qty={r['qty']}"


def _top_docks(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("docks-top")
def run(args):
    rows = store.load("docks")
    _top_docks(rows, args)
