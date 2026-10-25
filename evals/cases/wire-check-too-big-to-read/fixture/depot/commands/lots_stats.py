"""`depot lots-stats`: stats the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _stats_lots(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("lots-stats")
def run(args):
    rows = store.load("lots")
    _stats_lots(rows, args)
