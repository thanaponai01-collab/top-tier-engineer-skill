"""`depot items-search`: search the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} category={r['zone']} shelf={r['tag']} qty={r['qty']}"


def _search_items(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("items-search")
def run(args):
    rows = store.load("items")
    _search_items(rows, args)
