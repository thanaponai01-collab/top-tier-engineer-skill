"""`depot serials-top`: top the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} model={r['zone']} warranty={r['tag']} qty={r['qty']}"


def _top_serials(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("serials-top")
def run(args):
    rows = store.load("serials")
    _top_serials(rows, args)
