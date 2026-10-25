"""`depot hazmat-check`: check the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _check_hazmat(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("hazmat-check")
def run(args):
    rows = store.load("hazmat")
    _check_hazmat(rows, args)
