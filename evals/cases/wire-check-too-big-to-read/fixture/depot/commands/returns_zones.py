"""`depot returns-zones`: zones the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _zones_returns(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("returns-zones")
def run(args):
    rows = store.load("returns")
    _zones_returns(rows, args)
