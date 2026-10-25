"""`depot carriers-show`: show the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} region={r['zone']} service={r['tag']} qty={r['qty']}"


def _show_carriers(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("carriers-show")
def run(args):
    rows = store.load("carriers")
    _show_carriers(rows, args)
