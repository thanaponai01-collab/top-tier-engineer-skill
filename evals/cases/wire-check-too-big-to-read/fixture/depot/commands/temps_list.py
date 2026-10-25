"""`depot temps-list`: list the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} sensor={r['zone']} range={r['tag']} qty={r['qty']}"


def _list_temps(rows, args):
    for r in rows:
        print(_line(r))


@command("temps-list")
def run(args):
    rows = store.load("temps")
    _list_temps(rows, args)
