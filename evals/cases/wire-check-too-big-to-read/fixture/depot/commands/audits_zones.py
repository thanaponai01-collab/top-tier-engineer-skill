"""`depot audits-zones`: zones the audits records (auditor / scope)."""
from depot import store
from depot.registry import command



def _zones_audits(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("audits-zones")
def run(args):
    rows = store.load("audits")
    _zones_audits(rows, args)
