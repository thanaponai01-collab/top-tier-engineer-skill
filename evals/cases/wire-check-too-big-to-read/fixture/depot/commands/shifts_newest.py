"""`depot shifts-newest`: newest the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} lead={r['zone']} site={r['tag']} qty={r['qty']}"


def _newest_shifts(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("shifts-newest")
def run(args):
    rows = store.load("shifts")
    _newest_shifts(rows, args)
