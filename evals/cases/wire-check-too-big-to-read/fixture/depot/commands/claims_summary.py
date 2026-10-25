"""`depot claims-summary`: summary the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _summary_claims(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} claims, {total} units')


@command("claims-summary")
def run(args):
    rows = store.load("claims")
    _summary_claims(rows, args)
