"""`depot bins-stats`: stats the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _stats_bins(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("bins-stats")
def run(args):
    rows = store.load("bins")
    _stats_bins(rows, args)
