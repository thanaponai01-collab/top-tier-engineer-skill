"""`depot shifts-show`: show the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} lead={r['zone']} site={r['tag']} qty={r['qty']}"


def _show_shifts(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("shifts-show")
def run(args):
    rows = store.load("shifts")
    _show_shifts(rows, args)
