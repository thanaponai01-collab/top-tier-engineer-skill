"""`depot yards-stats`: stats the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _stats_yards(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("yards-stats")
def run(args):
    rows = store.load("yards")
    _stats_yards(rows, args)
