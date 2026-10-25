"""`depot lots-search`: search the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} batch={r['zone']} expiry={r['tag']} qty={r['qty']}"


def _search_lots(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("lots-search")
def run(args):
    rows = store.load("lots")
    _search_lots(rows, args)
