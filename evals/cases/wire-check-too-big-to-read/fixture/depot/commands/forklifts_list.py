"""`depot forklifts-list`: list the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} operator={r['zone']} battery={r['tag']} qty={r['qty']}"


def _list_forklifts(rows, args):
    for r in rows:
        print(_line(r))


@command("forklifts-list")
def run(args):
    rows = store.load("forklifts")
    _list_forklifts(rows, args)
