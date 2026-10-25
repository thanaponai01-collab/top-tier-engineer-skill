"""`depot temps-zones`: zones the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _zones_temps(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("temps-zones")
def run(args):
    rows = store.load("temps")
    _zones_temps(rows, args)
