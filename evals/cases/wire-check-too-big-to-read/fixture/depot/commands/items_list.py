"""`depot items-list`: list the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} category={r['zone']} shelf={r['tag']} qty={r['qty']}"


def _list_items(rows, args):
    for r in rows:
        print(_line(r))


@command("items-list")
def run(args):
    rows = store.load("items")
    _list_items(rows, args)
