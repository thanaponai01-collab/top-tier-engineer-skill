"""`depot temps-newest`: newest the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} sensor={r['zone']} range={r['tag']} qty={r['qty']}"


def _newest_temps(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("temps-newest")
def run(args):
    rows = store.load("temps")
    _newest_temps(rows, args)
