"""`depot temps-show`: show the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} sensor={r['zone']} range={r['tag']} qty={r['qty']}"


def _show_temps(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("temps-show")
def run(args):
    rows = store.load("temps")
    _show_temps(rows, args)
