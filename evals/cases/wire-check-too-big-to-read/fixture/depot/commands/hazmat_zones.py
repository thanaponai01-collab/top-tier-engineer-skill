"""`depot hazmat-zones`: zones the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _zones_hazmat(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("hazmat-zones")
def run(args):
    rows = store.load("hazmat")
    _zones_hazmat(rows, args)
