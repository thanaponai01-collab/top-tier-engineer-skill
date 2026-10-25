"""`depot transfers-zones`: zones the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _zones_transfers(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("transfers-zones")
def run(args):
    rows = store.load("transfers")
    _zones_transfers(rows, args)
