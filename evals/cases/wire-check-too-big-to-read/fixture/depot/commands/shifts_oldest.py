"""`depot shifts-oldest`: oldest the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} lead={r['zone']} site={r['tag']} qty={r['qty']}"


def _oldest_shifts(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("shifts-oldest")
def run(args):
    rows = store.load("shifts")
    _oldest_shifts(rows, args)
