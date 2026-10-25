"""`depot items-zones`: zones the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _zones_items(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("items-zones")
def run(args):
    rows = store.load("items")
    _zones_items(rows, args)
