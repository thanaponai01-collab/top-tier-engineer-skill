"""`depot zones-zones`: zones the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _zones_zones(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("zones-zones")
def run(args):
    rows = store.load("zones")
    _zones_zones(rows, args)
