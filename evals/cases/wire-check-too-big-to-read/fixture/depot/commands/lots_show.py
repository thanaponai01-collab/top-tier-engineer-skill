"""`depot lots-show`: show the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} batch={r['zone']} expiry={r['tag']} qty={r['qty']}"


def _show_lots(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("lots-show")
def run(args):
    rows = store.load("lots")
    _show_lots(rows, args)
