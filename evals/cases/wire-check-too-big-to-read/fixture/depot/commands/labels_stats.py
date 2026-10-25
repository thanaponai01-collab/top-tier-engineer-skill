"""`depot labels-stats`: stats the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _stats_labels(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("labels-stats")
def run(args):
    rows = store.load("labels")
    _stats_labels(rows, args)
