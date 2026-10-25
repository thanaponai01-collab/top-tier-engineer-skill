"""`depot serials-check`: check the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _check_serials(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("serials-check")
def run(args):
    rows = store.load("serials")
    _check_serials(rows, args)
