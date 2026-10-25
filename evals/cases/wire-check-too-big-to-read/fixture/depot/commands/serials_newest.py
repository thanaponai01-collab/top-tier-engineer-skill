"""`depot serials-newest`: newest the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} model={r['zone']} warranty={r['tag']} qty={r['qty']}"


def _newest_serials(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("serials-newest")
def run(args):
    rows = store.load("serials")
    _newest_serials(rows, args)
