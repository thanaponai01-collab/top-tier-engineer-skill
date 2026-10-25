"""`depot labels-zones`: zones the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _zones_labels(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("labels-zones")
def run(args):
    rows = store.load("labels")
    _zones_labels(rows, args)
