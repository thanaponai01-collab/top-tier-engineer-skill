"""`depot shifts-top`: top the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} lead={r['zone']} site={r['tag']} qty={r['qty']}"


def _top_shifts(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("shifts-top")
def run(args):
    rows = store.load("shifts")
    _top_shifts(rows, args)
