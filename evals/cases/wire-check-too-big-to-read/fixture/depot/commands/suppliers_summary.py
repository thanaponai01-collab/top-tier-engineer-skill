"""`depot suppliers-summary`: summary the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _summary_suppliers(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} suppliers, {total} units')


@command("suppliers-summary")
def run(args):
    rows = store.load("suppliers")
    _summary_suppliers(rows, args)
