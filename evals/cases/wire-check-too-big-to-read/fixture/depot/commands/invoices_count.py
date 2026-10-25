"""`depot invoices-count`: count the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _count_invoices(rows, args):
    print(len(rows))


@command("invoices-count")
def run(args):
    rows = store.load("invoices")
    _count_invoices(rows, args)
