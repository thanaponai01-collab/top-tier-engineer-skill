"""`depot orders-list`: list the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} customer={r['zone']} channel={r['tag']} qty={r['qty']}"


def _list_orders(rows, args):
    for r in rows:
        print(_line(r))


@command("orders-list")
def run(args):
    rows = store.load("orders")
    _list_orders(rows, args)
