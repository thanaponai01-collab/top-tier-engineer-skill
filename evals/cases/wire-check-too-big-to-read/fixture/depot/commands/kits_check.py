"""`depot kits-check`: check the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _check_kits(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("kits-check")
def run(args):
    rows = store.load("kits")
    _check_kits(rows, args)
