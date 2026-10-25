"""`depot cycle-check`: check the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _check_cycle(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("cycle-check")
def run(args):
    rows = store.load("cycle")
    _check_cycle(rows, args)
