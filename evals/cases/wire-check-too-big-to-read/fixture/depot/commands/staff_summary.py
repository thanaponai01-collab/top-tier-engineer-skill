"""`depot staff-summary`: summary the staff records (team / role)."""
from depot import store
from depot.registry import command



def _summary_staff(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} staff, {total} units')


@command("staff-summary")
def run(args):
    rows = store.load("staff")
    _summary_staff(rows, args)
