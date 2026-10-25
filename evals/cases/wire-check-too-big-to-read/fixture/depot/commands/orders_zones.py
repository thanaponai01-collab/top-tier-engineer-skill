"""`depot orders-zones`: zones the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _zones_orders(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("orders-zones")
def run(args):
    rows = store.load("orders")
    _zones_orders(rows, args)
