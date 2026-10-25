"""`depot bins-zones`: zones the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _zones_bins(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("bins-zones")
def run(args):
    rows = store.load("bins")
    _zones_bins(rows, args)
