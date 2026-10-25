"""`depot orders-top`: top the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} customer={r['zone']} channel={r['tag']} qty={r['qty']}"


def _top_orders(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("orders-top")
def run(args):
    rows = store.load("orders")
    _top_orders(rows, args)
