"""`depot returns-show`: show the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} reason={r['zone']} grade={r['tag']} qty={r['qty']}"


def _show_returns(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("returns-show")
def run(args):
    rows = store.load("returns")
    _show_returns(rows, args)
