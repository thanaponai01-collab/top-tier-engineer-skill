"""`depot seals-top`: top the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} trailer={r['zone']} inspector={r['tag']} qty={r['qty']}"


def _top_seals(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("seals-top")
def run(args):
    rows = store.load("seals")
    _top_seals(rows, args)
