"""`depot bins-summary`: summary the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _summary_bins(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} bins, {total} units')


@command("bins-summary")
def run(args):
    rows = store.load("bins")
    _summary_bins(rows, args)
