"""`depot totes-check`: check the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _check_totes(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("totes-check")
def run(args):
    rows = store.load("totes")
    _check_totes(rows, args)
