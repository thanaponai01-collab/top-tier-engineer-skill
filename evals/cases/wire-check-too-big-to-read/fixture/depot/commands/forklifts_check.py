"""`depot forklifts-check`: check the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _check_forklifts(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("forklifts-check")
def run(args):
    rows = store.load("forklifts")
    _check_forklifts(rows, args)
