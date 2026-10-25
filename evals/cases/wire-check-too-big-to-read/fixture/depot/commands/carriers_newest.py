"""`depot carriers-newest`: newest the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} region={r['zone']} service={r['tag']} qty={r['qty']}"


def _newest_carriers(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("carriers-newest")
def run(args):
    rows = store.load("carriers")
    _newest_carriers(rows, args)
