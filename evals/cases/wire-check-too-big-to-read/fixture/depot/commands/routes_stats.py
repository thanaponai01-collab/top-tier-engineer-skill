"""`depot routes-stats`: stats the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _stats_routes(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("routes-stats")
def run(args):
    rows = store.load("routes")
    _stats_routes(rows, args)
