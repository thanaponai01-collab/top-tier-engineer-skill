"""`depot orders-show`: show the orders records (customer / channel)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} customer={r['zone']} channel={r['tag']} qty={r['qty']}"


def _show_orders(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("orders-show")
def run(args):
    rows = store.load("orders")
    _show_orders(rows, args)
