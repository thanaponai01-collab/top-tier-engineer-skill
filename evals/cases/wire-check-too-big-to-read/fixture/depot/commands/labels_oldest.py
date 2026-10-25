"""`depot labels-oldest`: oldest the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} printer={r['zone']} format={r['tag']} qty={r['qty']}"


def _oldest_labels(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("labels-oldest")
def run(args):
    rows = store.load("labels")
    _oldest_labels(rows, args)
