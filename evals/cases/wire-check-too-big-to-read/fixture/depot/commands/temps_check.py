"""`depot temps-check`: check the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _check_temps(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("temps-check")
def run(args):
    rows = store.load("temps")
    _check_temps(rows, args)
