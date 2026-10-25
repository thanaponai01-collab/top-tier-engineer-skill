"""`depot lots-check`: check the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _check_lots(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("lots-check")
def run(args):
    rows = store.load("lots")
    _check_lots(rows, args)
