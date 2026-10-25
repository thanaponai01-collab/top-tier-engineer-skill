"""`depot totes-stats`: stats the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _stats_totes(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("totes-stats")
def run(args):
    rows = store.load("totes")
    _stats_totes(rows, args)
