"""`depot labels-show`: show the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} printer={r['zone']} format={r['tag']} qty={r['qty']}"


def _show_labels(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("labels-show")
def run(args):
    rows = store.load("labels")
    _show_labels(rows, args)
