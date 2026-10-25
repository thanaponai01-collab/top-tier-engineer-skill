"""`depot seals-stats`: stats the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _stats_seals(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("seals-stats")
def run(args):
    rows = store.load("seals")
    _stats_seals(rows, args)
