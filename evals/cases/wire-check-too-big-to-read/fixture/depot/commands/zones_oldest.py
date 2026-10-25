"""`depot zones-oldest`: oldest the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} manager={r['zone']} floor={r['tag']} qty={r['qty']}"


def _oldest_zones(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("zones-oldest")
def run(args):
    rows = store.load("zones")
    _oldest_zones(rows, args)
