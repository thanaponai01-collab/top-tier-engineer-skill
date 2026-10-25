"""`depot forklifts-zones`: zones the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _zones_forklifts(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("forklifts-zones")
def run(args):
    rows = store.load("forklifts")
    _zones_forklifts(rows, args)
