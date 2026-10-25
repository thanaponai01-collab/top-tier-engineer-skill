"""`depot kits-list`: list the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} bundle={r['zone']} station={r['tag']} qty={r['qty']}"


def _list_kits(rows, args):
    for r in rows:
        print(_line(r))


@command("kits-list")
def run(args):
    rows = store.load("kits")
    _list_kits(rows, args)
