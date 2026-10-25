"""`depot kits-newest`: newest the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} bundle={r['zone']} station={r['tag']} qty={r['qty']}"


def _newest_kits(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("kits-newest")
def run(args):
    rows = store.load("kits")
    _newest_kits(rows, args)
