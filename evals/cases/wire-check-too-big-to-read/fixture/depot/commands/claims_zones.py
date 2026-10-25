"""`depot claims-zones`: zones the claims records (insurer / status)."""
from depot import store
from depot.registry import command



def _zones_claims(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("claims-zones")
def run(args):
    rows = store.load("claims")
    _zones_claims(rows, args)
