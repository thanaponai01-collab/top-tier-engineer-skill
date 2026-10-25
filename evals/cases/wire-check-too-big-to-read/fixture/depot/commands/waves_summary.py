"""`depot waves-summary`: summary the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _summary_waves(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} waves, {total} units')


@command("waves-summary")
def run(args):
    rows = store.load("waves")
    _summary_waves(rows, args)
