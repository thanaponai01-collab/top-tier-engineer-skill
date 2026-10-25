"""`depot items-show`: show the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} category={r['zone']} shelf={r['tag']} qty={r['qty']}"


def _show_items(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("items-show")
def run(args):
    rows = store.load("items")
    _show_items(rows, args)
