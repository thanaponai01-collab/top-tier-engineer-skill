"""`depot routes-check`: check the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _check_routes(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("routes-check")
def run(args):
    rows = store.load("routes")
    _check_routes(rows, args)
