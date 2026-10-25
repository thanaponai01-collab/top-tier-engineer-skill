"""`depot temps-top`: top the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} sensor={r['zone']} range={r['tag']} qty={r['qty']}"


def _top_temps(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("temps-top")
def run(args):
    rows = store.load("temps")
    _top_temps(rows, args)
