"""`depot docks-search`: search the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} yard={r['zone']} slot={r['tag']} qty={r['qty']}"


def _search_docks(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("docks-search")
def run(args):
    rows = store.load("docks")
    _search_docks(rows, args)
