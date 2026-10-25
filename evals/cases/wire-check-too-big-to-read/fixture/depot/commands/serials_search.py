"""`depot serials-search`: search the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} model={r['zone']} warranty={r['tag']} qty={r['qty']}"


def _search_serials(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("serials-search")
def run(args):
    rows = store.load("serials")
    _search_serials(rows, args)
