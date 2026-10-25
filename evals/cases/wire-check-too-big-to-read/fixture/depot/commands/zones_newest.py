"""`depot zones-newest`: newest the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} manager={r['zone']} floor={r['tag']} qty={r['qty']}"


def _newest_zones(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("zones-newest")
def run(args):
    rows = store.load("zones")
    _newest_zones(rows, args)
