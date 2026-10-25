"""`depot transfers-search`: search the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} origin={r['zone']} dest={r['tag']} qty={r['qty']}"


def _search_transfers(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("transfers-search")
def run(args):
    rows = store.load("transfers")
    _search_transfers(rows, args)
