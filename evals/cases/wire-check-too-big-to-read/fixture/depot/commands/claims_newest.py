"""`depot claims-newest`: newest the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} insurer={r['zone']} status={r['tag']} qty={r['qty']}"


def _newest_claims(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("claims-newest")
def run(args):
    rows = store.load("claims")
    _newest_claims(rows, args)
