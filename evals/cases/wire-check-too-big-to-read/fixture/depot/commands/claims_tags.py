"""`depot claims-tags`: tags the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _tags_claims(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("claims-tags")
def run(args):
    rows = store.load("claims")
    _tags_claims(rows, args)
