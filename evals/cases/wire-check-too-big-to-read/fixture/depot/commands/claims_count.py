"""`depot claims-count`: count the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _count_claims(rows, args):
    print(len(rows))


@command("claims-count")
def run(args):
    rows = store.load("claims")
    _count_claims(rows, args)
