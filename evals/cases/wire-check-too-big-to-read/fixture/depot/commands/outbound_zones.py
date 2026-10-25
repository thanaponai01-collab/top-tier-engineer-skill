"""`depot outbound-zones`: zones the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _zones_outbound(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("outbound-zones")
def run(args):
    rows = store.load("outbound")
    _zones_outbound(rows, args)
