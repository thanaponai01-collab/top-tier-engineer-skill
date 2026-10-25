"""`depot items-oldest`: oldest the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} category={r['zone']} shelf={r['tag']} qty={r['qty']}"


def _oldest_items(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("items-oldest")
def run(args):
    rows = store.load("items")
    _oldest_items(rows, args)
