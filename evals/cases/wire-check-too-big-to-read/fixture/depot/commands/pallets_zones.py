"""`depot pallets-zones`: zones the pallets records (owner / rack)."""
from depot import store
from depot.registry import command



def _zones_pallets(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("pallets-zones")
def run(args):
    rows = store.load("pallets")
    _zones_pallets(rows, args)
