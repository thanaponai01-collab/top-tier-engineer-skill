"""`depot invoices-newest`: newest the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} payer={r['zone']} currency={r['tag']} qty={r['qty']}"


def _newest_invoices(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("invoices-newest")
def run(args):
    rows = store.load("invoices")
    _newest_invoices(rows, args)
