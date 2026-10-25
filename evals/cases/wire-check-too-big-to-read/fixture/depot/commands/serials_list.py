"""`depot serials-list`: list the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} model={r['zone']} warranty={r['tag']} qty={r['qty']}"


def _list_serials(rows, args):
    for r in rows:
        print(_line(r))


@command("serials-list")
def run(args):
    rows = store.load("serials")
    _list_serials(rows, args)
