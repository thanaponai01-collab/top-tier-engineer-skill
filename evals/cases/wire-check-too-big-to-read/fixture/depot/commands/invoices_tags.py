"""`depot invoices-tags`: tags the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _tags_invoices(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("invoices-tags")
def run(args):
    rows = store.load("invoices")
    _tags_invoices(rows, args)
