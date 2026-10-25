"""`depot returns-check`: check the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _check_returns(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("returns-check")
def run(args):
    rows = store.load("returns")
    _check_returns(rows, args)
