"""`depot items-top`: top the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} category={r['zone']} shelf={r['tag']} qty={r['qty']}"


def _top_items(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("items-top")
def run(args):
    rows = store.load("items")
    _top_items(rows, args)
