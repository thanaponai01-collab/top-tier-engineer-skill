"""`depot staff-check`: check the staff records (team / role)."""
from depot import store
from depot.registry import command



def _check_staff(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("staff-check")
def run(args):
    rows = store.load("staff")
    _check_staff(rows, args)
