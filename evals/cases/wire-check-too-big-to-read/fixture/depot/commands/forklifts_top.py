"""`depot forklifts-top`: top the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} operator={r['zone']} battery={r['tag']} qty={r['qty']}"


def _top_forklifts(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("forklifts-top")
def run(args):
    rows = store.load("forklifts")
    _top_forklifts(rows, args)
