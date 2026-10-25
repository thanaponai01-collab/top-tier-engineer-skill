"""`depot forklifts-summary`: summary the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _summary_forklifts(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} forklifts, {total} units')


@command("forklifts-summary")
def run(args):
    rows = store.load("forklifts")
    _summary_forklifts(rows, args)
