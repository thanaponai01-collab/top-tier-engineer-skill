"""`depot shifts-zones`: zones the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _zones_shifts(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("shifts-zones")
def run(args):
    rows = store.load("shifts")
    _zones_shifts(rows, args)
