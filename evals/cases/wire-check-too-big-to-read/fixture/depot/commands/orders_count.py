"""`depot orders-count`: count the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _count_orders(rows, args):
    print(len(rows))


@command("orders-count")
def run(args):
    rows = store.load("orders")
    _count_orders(rows, args)
