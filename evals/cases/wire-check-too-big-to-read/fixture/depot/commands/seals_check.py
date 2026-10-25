"""`depot seals-check`: check the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _check_seals(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("seals-check")
def run(args):
    rows = store.load("seals")
    _check_seals(rows, args)
