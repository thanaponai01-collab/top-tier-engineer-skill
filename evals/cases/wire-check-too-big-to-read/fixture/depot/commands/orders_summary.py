"""`depot orders-summary`: summary the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _summary_orders(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} orders, {total} units')


@command("orders-summary")
def run(args):
    rows = store.load("orders")
    _summary_orders(rows, args)
