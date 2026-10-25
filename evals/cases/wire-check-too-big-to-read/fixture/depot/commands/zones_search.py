"""`depot zones-search`: search the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} manager={r['zone']} floor={r['tag']} qty={r['qty']}"


def _search_zones(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("zones-search")
def run(args):
    rows = store.load("zones")
    _search_zones(rows, args)
