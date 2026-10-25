"""`depot inbound-zones`: zones the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _zones_inbound(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("inbound-zones")
def run(args):
    rows = store.load("inbound")
    _zones_inbound(rows, args)
