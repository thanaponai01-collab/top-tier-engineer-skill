"""`depot invoices-oldest`: oldest the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} payer={r['zone']} currency={r['tag']} qty={r['qty']}"


def _oldest_invoices(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("invoices-oldest")
def run(args):
    rows = store.load("invoices")
    _oldest_invoices(rows, args)
