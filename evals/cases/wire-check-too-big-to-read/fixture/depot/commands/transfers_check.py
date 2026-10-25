"""`depot transfers-check`: check the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _check_transfers(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("transfers-check")
def run(args):
    rows = store.load("transfers")
    _check_transfers(rows, args)
