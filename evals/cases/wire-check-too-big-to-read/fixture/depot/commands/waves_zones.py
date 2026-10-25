"""`depot waves-zones`: zones the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _zones_waves(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("waves-zones")
def run(args):
    rows = store.load("waves")
    _zones_waves(rows, args)
