"""`depot zones-show`: show the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} manager={r['zone']} floor={r['tag']} qty={r['qty']}"


def _show_zones(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("zones-show")
def run(args):
    rows = store.load("zones")
    _show_zones(rows, args)
