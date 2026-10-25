"""`depot staff-zones`: zones the staff records (team / role)."""
from depot import store
from depot.registry import command



def _zones_staff(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("staff-zones")
def run(args):
    rows = store.load("staff")
    _zones_staff(rows, args)
