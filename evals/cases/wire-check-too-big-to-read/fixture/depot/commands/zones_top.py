"""`depot zones-top`: top the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} manager={r['zone']} floor={r['tag']} qty={r['qty']}"


def _top_zones(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("zones-top")
def run(args):
    rows = store.load("zones")
    _top_zones(rows, args)
