"""`depot invoices-list`: list the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} payer={r['zone']} currency={r['tag']} qty={r['qty']}"


def _list_invoices(rows, args):
    for r in rows:
        print(_line(r))


@command("invoices-list")
def run(args):
    rows = store.load("invoices")
    _list_invoices(rows, args)
