"""`depot carriers-zones`: zones the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _zones_carriers(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("carriers-zones")
def run(args):
    rows = store.load("carriers")
    _zones_carriers(rows, args)
