"""`depot forklifts-stats`: stats the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _stats_forklifts(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("forklifts-stats")
def run(args):
    rows = store.load("forklifts")
    _stats_forklifts(rows, args)
