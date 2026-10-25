"""`depot carriers-oldest`: oldest the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} region={r['zone']} service={r['tag']} qty={r['qty']}"


def _oldest_carriers(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("carriers-oldest")
def run(args):
    rows = store.load("carriers")
    _oldest_carriers(rows, args)
