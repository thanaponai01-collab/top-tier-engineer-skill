"""`depot invoices-summary`: summary the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _summary_invoices(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} invoices, {total} units')


@command("invoices-summary")
def run(args):
    rows = store.load("invoices")
    _summary_invoices(rows, args)
