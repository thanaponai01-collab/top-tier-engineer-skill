"""`depot totes-show`: show the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} color={r['zone']} lane={r['tag']} qty={r['qty']}"


def _show_totes(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("totes-show")
def run(args):
    rows = store.load("totes")
    _show_totes(rows, args)
