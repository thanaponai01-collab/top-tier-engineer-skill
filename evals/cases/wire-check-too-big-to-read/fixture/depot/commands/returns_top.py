"""`depot returns-top`: top the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} reason={r['zone']} grade={r['tag']} qty={r['qty']}"


def _top_returns(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("returns-top")
def run(args):
    rows = store.load("returns")
    _top_returns(rows, args)
