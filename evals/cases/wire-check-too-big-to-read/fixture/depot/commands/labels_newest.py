"""`depot labels-newest`: newest the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} printer={r['zone']} format={r['tag']} qty={r['qty']}"


def _newest_labels(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("labels-newest")
def run(args):
    rows = store.load("labels")
    _newest_labels(rows, args)
