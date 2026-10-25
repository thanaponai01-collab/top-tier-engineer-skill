"""`depot kits-search`: search the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} bundle={r['zone']} station={r['tag']} qty={r['qty']}"


def _search_kits(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("kits-search")
def run(args):
    rows = store.load("kits")
    _search_kits(rows, args)
