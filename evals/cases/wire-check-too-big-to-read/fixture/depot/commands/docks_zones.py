"""`depot docks-zones`: zones the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _zones_docks(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("docks-zones")
def run(args):
    rows = store.load("docks")
    _zones_docks(rows, args)
