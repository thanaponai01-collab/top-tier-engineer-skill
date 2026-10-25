"""`depot serials-show`: show the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} model={r['zone']} warranty={r['tag']} qty={r['qty']}"


def _show_serials(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("serials-show")
def run(args):
    rows = store.load("serials")
    _show_serials(rows, args)
