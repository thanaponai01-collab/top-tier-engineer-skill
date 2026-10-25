"""`depot orders-newest`: newest the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} customer={r['zone']} channel={r['tag']} qty={r['qty']}"


def _newest_orders(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("orders-newest")
def run(args):
    rows = store.load("orders")
    _newest_orders(rows, args)
