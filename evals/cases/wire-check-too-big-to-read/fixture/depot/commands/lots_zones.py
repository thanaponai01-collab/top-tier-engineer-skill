"""`depot lots-zones`: zones the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _zones_lots(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("lots-zones")
def run(args):
    rows = store.load("lots")
    _zones_lots(rows, args)
