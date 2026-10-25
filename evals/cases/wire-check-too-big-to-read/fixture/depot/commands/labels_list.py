"""`depot labels-list`: list the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} printer={r['zone']} format={r['tag']} qty={r['qty']}"


def _list_labels(rows, args):
    for r in rows:
        print(_line(r))


@command("labels-list")
def run(args):
    rows = store.load("labels")
    _list_labels(rows, args)
