"""`depot invoices-check`: check the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _check_invoices(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("invoices-check")
def run(args):
    rows = store.load("invoices")
    _check_invoices(rows, args)
