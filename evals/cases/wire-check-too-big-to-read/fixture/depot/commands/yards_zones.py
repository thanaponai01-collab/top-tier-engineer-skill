"""`depot yards-zones`: zones the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _zones_yards(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("yards-zones")
def run(args):
    rows = store.load("yards")
    _zones_yards(rows, args)
