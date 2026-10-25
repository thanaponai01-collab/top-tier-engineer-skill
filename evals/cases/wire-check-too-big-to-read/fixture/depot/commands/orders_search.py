"""`depot orders-search`: search the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} customer={r['zone']} channel={r['tag']} qty={r['qty']}"


def _search_orders(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("orders-search")
def run(args):
    rows = store.load("orders")
    _search_orders(rows, args)
