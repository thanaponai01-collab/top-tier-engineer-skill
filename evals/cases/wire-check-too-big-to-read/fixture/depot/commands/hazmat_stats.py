"""`depot hazmat-stats`: stats the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _stats_hazmat(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("hazmat-stats")
def run(args):
    rows = store.load("hazmat")
    _stats_hazmat(rows, args)
