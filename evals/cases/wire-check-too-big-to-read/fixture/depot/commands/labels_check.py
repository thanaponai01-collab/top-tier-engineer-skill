"""`depot labels-check`: check the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _check_labels(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("labels-check")
def run(args):
    rows = store.load("labels")
    _check_labels(rows, args)
