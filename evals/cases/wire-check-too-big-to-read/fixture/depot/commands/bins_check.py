"""`depot bins-check`: check the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _check_bins(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("bins-check")
def run(args):
    rows = store.load("bins")
    _check_bins(rows, args)
