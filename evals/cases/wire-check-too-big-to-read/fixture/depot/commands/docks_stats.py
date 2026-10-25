"""`depot docks-stats`: stats the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _stats_docks(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("docks-stats")
def run(args):
    rows = store.load("docks")
    _stats_docks(rows, args)
