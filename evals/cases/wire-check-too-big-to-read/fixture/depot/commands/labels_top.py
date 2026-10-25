"""`depot labels-top`: top the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} printer={r['zone']} format={r['tag']} qty={r['qty']}"


def _top_labels(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("labels-top")
def run(args):
    rows = store.load("labels")
    _top_labels(rows, args)
