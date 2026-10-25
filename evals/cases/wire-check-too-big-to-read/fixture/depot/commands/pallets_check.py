"""`depot pallets-check`: check the pallets records (owner / rack)."""
from depot import store
from depot.registry import command



def _check_pallets(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("pallets-check")
def run(args):
    rows = store.load("pallets")
    _check_pallets(rows, args)
