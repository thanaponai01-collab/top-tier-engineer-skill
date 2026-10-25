"""`depot suppliers-zones`: zones the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _zones_suppliers(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("suppliers-zones")
def run(args):
    rows = store.load("suppliers")
    _zones_suppliers(rows, args)
