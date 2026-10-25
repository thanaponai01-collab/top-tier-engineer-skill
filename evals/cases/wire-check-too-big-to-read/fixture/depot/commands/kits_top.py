"""`depot kits-top`: top the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} bundle={r['zone']} station={r['tag']} qty={r['qty']}"


def _top_kits(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("kits-top")
def run(args):
    rows = store.load("kits")
    _top_kits(rows, args)
