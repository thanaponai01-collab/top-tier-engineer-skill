"""`depot cycle-search`: search the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} counter={r['zone']} shift={r['tag']} qty={r['qty']}"


def _search_cycle(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("cycle-search")
def run(args):
    rows = store.load("cycle")
    _search_cycle(rows, args)
