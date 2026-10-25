"""`depot returns-list`: list the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} reason={r['zone']} grade={r['tag']} qty={r['qty']}"


def _list_returns(rows, args):
    for r in rows:
        print(_line(r))


@command("returns-list")
def run(args):
    rows = store.load("returns")
    _list_returns(rows, args)
