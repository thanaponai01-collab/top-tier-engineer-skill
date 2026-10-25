"""`depot yards-check`: check the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _check_yards(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("yards-check")
def run(args):
    rows = store.load("yards")
    _check_yards(rows, args)
