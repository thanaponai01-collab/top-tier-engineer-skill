"""`depot cycle-zones`: zones the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _zones_cycle(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("cycle-zones")
def run(args):
    rows = store.load("cycle")
    _zones_cycle(rows, args)
