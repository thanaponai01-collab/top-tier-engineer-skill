"""`depot orders-check`: check the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _check_orders(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("orders-check")
def run(args):
    rows = store.load("orders")
    _check_orders(rows, args)
