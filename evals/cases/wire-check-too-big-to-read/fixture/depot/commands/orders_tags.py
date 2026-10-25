"""`depot orders-tags`: tags the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _tags_orders(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("orders-tags")
def run(args):
    rows = store.load("orders")
    _tags_orders(rows, args)
