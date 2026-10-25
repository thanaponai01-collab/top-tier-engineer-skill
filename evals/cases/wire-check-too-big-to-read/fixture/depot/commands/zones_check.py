"""`depot zones-check`: check the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _check_zones(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("zones-check")
def run(args):
    rows = store.load("zones")
    _check_zones(rows, args)
