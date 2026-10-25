"""`depot claims-stats`: stats the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _stats_claims(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("claims-stats")
def run(args):
    rows = store.load("claims")
    _stats_claims(rows, args)
