"""`depot claims-top`: top the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} insurer={r['zone']} status={r['tag']} qty={r['qty']}"


def _top_claims(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("claims-top")
def run(args):
    rows = store.load("claims")
    _top_claims(rows, args)
