"""`depot seals-show`: show the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} trailer={r['zone']} inspector={r['tag']} qty={r['qty']}"


def _show_seals(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("seals-show")
def run(args):
    rows = store.load("seals")
    _show_seals(rows, args)
