"""`depot waves-check`: check the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _check_waves(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("waves-check")
def run(args):
    rows = store.load("waves")
    _check_waves(rows, args)
