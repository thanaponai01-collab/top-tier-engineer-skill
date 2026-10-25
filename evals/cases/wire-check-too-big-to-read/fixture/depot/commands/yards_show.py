"""`depot yards-show`: show the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} gate={r['zone']} spot={r['tag']} qty={r['qty']}"


def _show_yards(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("yards-show")
def run(args):
    rows = store.load("yards")
    _show_yards(rows, args)
