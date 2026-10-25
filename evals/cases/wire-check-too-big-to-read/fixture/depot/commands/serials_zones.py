"""`depot serials-zones`: zones the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _zones_serials(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("serials-zones")
def run(args):
    rows = store.load("serials")
    _zones_serials(rows, args)
