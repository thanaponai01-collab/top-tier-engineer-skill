"""`depot carriers-check`: check the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _check_carriers(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("carriers-check")
def run(args):
    rows = store.load("carriers")
    _check_carriers(rows, args)
