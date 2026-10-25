"""`depot invoices-zones`: zones the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _zones_invoices(rows, args):
    by = {}
    for r in rows:
        by[r['zone']] = by.get(r['zone'], 0) + r['qty']
    for z in sorted(by):
        print(z, by[z])


@command("invoices-zones")
def run(args):
    rows = store.load("invoices")
    _zones_invoices(rows, args)
