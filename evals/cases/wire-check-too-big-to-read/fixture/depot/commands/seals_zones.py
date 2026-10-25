"""`depot seals-zones`: zones the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _zones_seals(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("seals-zones")
def run(args):
    rows = store.load("seals")
    _zones_seals(rows, args)
