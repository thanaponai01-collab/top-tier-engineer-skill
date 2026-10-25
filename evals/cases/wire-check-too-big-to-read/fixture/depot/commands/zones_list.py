"""`depot zones-list`: list the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} manager={r['zone']} floor={r['tag']} qty={r['qty']}"


def _list_zones(rows, args):
    for r in rows:
        print(_line(r))


@command("zones-list")
def run(args):
    rows = store.load("zones")
    _list_zones(rows, args)
