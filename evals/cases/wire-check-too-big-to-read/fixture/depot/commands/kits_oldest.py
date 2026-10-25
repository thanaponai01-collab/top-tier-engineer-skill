"""`depot kits-oldest`: oldest the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} bundle={r['zone']} station={r['tag']} qty={r['qty']}"


def _oldest_kits(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("kits-oldest")
def run(args):
    rows = store.load("kits")
    _oldest_kits(rows, args)
