"""`depot claims-list`: list the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} insurer={r['zone']} status={r['tag']} qty={r['qty']}"


def _list_claims(rows, args):
    for r in rows:
        print(_line(r))


@command("claims-list")
def run(args):
    rows = store.load("claims")
    _list_claims(rows, args)
