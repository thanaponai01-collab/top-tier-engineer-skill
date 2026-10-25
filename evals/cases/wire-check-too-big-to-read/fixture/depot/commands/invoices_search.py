"""`depot invoices-search`: search the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} payer={r['zone']} currency={r['tag']} qty={r['qty']}"


def _search_invoices(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("invoices-search")
def run(args):
    rows = store.load("invoices")
    _search_invoices(rows, args)
