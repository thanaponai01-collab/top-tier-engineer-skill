"""`depot cycle-stats`: stats the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _stats_cycle(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("cycle-stats")
def run(args):
    rows = store.load("cycle")
    _stats_cycle(rows, args)
