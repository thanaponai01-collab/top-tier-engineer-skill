"""`depot hazmat-show`: show the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} class={r['zone']} placard={r['tag']} qty={r['qty']}"


def _show_hazmat(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("hazmat-show")
def run(args):
    rows = store.load("hazmat")
    _show_hazmat(rows, args)
