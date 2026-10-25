"""`depot transfers-top`: top the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} origin={r['zone']} dest={r['tag']} qty={r['qty']}"


def _top_transfers(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("transfers-top")
def run(args):
    rows = store.load("transfers")
    _top_transfers(rows, args)
