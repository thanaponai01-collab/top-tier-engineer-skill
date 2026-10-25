"""`depot transfers-stats`: stats the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _stats_transfers(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("transfers-stats")
def run(args):
    rows = store.load("transfers")
    _stats_transfers(rows, args)
