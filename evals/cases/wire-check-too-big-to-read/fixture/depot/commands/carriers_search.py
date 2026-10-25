"""`depot carriers-search`: search the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} region={r['zone']} service={r['tag']} qty={r['qty']}"


def _search_carriers(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("carriers-search")
def run(args):
    rows = store.load("carriers")
    _search_carriers(rows, args)
