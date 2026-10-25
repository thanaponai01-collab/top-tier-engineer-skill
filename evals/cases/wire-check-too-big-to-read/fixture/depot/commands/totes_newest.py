"""`depot totes-newest`: newest the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} color={r['zone']} lane={r['tag']} qty={r['qty']}"


def _newest_totes(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("totes-newest")
def run(args):
    rows = store.load("totes")
    _newest_totes(rows, args)
