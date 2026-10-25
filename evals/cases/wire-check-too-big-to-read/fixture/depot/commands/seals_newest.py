"""`depot seals-newest`: newest the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} trailer={r['zone']} inspector={r['tag']} qty={r['qty']}"


def _newest_seals(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("seals-newest")
def run(args):
    rows = store.load("seals")
    _newest_seals(rows, args)
