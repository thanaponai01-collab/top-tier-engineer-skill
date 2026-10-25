"""`depot shifts-summary`: summary the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _summary_shifts(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} shifts, {total} units')


@command("shifts-summary")
def run(args):
    rows = store.load("shifts")
    _summary_shifts(rows, args)
