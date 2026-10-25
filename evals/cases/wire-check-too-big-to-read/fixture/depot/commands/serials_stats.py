"""`depot serials-stats`: stats the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _stats_serials(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("serials-stats")
def run(args):
    rows = store.load("serials")
    _stats_serials(rows, args)
