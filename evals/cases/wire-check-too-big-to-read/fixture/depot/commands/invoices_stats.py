"""`depot invoices-stats`: stats the invoices records (payer / currency)."""
from depot import store
from depot.registry import command



def _stats_invoices(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("invoices-stats")
def run(args):
    rows = store.load("invoices")
    _stats_invoices(rows, args)
