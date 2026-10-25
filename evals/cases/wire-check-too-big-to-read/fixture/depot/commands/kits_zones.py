"""`depot kits-zones`: zones the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _zones_kits(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("kits-zones")
def run(args):
    rows = store.load("kits")
    _zones_kits(rows, args)
