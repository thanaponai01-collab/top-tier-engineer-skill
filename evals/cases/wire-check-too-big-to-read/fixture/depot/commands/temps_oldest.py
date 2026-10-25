"""`depot temps-oldest`: oldest the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} sensor={r['zone']} range={r['tag']} qty={r['qty']}"


def _oldest_temps(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("temps-oldest")
def run(args):
    rows = store.load("temps")
    _oldest_temps(rows, args)
