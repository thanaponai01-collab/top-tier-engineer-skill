"""`depot claims-check`: check the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _check_claims(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("claims-check")
def run(args):
    rows = store.load("claims")
    _check_claims(rows, args)
