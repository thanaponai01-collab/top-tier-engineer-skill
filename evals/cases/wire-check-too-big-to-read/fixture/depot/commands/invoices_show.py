"""`depot invoices-show`: show the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} payer={r['zone']} currency={r['tag']} qty={r['qty']}"


def _show_invoices(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("invoices-show")
def run(args):
    rows = store.load("invoices")
    _show_invoices(rows, args)
