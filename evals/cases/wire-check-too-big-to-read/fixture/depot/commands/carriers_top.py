"""`depot carriers-top`: top the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} region={r['zone']} service={r['tag']} qty={r['qty']}"


def _top_carriers(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("carriers-top")
def run(args):
    rows = store.load("carriers")
    _top_carriers(rows, args)
