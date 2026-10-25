"""`depot carriers-list`: list the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} region={r['zone']} service={r['tag']} qty={r['qty']}"


def _list_carriers(rows, args):
    for r in rows:
        print(_line(r))


@command("carriers-list")
def run(args):
    rows = store.load("carriers")
    _list_carriers(rows, args)
