"""`depot returns-oldest`: oldest the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} reason={r['zone']} grade={r['tag']} qty={r['qty']}"


def _oldest_returns(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("returns-oldest")
def run(args):
    rows = store.load("returns")
    _oldest_returns(rows, args)
