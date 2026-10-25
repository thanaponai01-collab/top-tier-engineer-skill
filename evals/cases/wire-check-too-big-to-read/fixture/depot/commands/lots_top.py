"""`depot lots-top`: top the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} batch={r['zone']} expiry={r['tag']} qty={r['qty']}"


def _top_lots(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("lots-top")
def run(args):
    rows = store.load("lots")
    _top_lots(rows, args)
