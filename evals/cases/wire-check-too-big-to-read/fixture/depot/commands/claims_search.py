"""`depot claims-search`: search the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} insurer={r['zone']} status={r['tag']} qty={r['qty']}"


def _search_claims(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("claims-search")
def run(args):
    rows = store.load("claims")
    _search_claims(rows, args)
