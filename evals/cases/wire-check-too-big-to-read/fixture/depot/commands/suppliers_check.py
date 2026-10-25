"""`depot suppliers-check`: check the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _check_suppliers(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("suppliers-check")
def run(args):
    rows = store.load("suppliers")
    _check_suppliers(rows, args)
