"""`depot returns-search`: search the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} reason={r['zone']} grade={r['tag']} qty={r['qty']}"


def _search_returns(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("returns-search")
def run(args):
    rows = store.load("returns")
    _search_returns(rows, args)
