"""`depot items-check`: check the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _check_items(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("items-check")
def run(args):
    rows = store.load("items")
    _check_items(rows, args)
