"""`depot labels-search`: search the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} printer={r['zone']} format={r['tag']} qty={r['qty']}"


def _search_labels(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("labels-search")
def run(args):
    rows = store.load("labels")
    _search_labels(rows, args)
