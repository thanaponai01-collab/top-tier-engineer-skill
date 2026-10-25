"""`depot shifts-stats`: stats the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _stats_shifts(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("shifts-stats")
def run(args):
    rows = store.load("shifts")
    _stats_shifts(rows, args)
