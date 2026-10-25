"""`depot cycle-show`: show the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} counter={r['zone']} shift={r['tag']} qty={r['qty']}"


def _show_cycle(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("cycle-show")
def run(args):
    rows = store.load("cycle")
    _show_cycle(rows, args)
