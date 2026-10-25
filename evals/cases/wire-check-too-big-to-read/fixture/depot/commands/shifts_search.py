"""`depot shifts-search`: search the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} lead={r['zone']} site={r['tag']} qty={r['qty']}"


def _search_shifts(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("shifts-search")
def run(args):
    rows = store.load("shifts")
    _search_shifts(rows, args)
