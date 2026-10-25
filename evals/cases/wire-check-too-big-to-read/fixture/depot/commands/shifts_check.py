"""`depot shifts-check`: check the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _check_shifts(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("shifts-check")
def run(args):
    rows = store.load("shifts")
    _check_shifts(rows, args)
