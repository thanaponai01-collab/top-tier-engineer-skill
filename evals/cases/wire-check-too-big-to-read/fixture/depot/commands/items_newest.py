"""`depot items-newest`: newest the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} category={r['zone']} shelf={r['tag']} qty={r['qty']}"


def _newest_items(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("items-newest")
def run(args):
    rows = store.load("items")
    _newest_items(rows, args)
