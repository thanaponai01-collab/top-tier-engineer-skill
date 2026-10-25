"""`depot totes-zones`: zones the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _zones_totes(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("totes-zones")
def run(args):
    rows = store.load("totes")
    _zones_totes(rows, args)
