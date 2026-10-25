"""`depot serials-oldest`: oldest the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} model={r['zone']} warranty={r['tag']} qty={r['qty']}"


def _oldest_serials(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("serials-oldest")
def run(args):
    rows = store.load("serials")
    _oldest_serials(rows, args)
