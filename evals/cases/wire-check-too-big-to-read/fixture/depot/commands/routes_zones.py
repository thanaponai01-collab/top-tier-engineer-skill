"""`depot routes-zones`: zones the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _zones_routes(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("routes-zones")
def run(args):
    rows = store.load("routes")
    _zones_routes(rows, args)
