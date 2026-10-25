"""`depot docks-check`: check the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _check_docks(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("docks-check")
def run(args):
    rows = store.load("docks")
    _check_docks(rows, args)
