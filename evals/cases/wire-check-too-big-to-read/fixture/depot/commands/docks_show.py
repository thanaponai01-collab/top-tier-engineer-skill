"""`depot docks-show`: show the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} yard={r['zone']} slot={r['tag']} qty={r['qty']}"


def _show_docks(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("docks-show")
def run(args):
    rows = store.load("docks")
    _show_docks(rows, args)
