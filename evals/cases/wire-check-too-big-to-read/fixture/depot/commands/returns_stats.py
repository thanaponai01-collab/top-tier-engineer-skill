"""`depot returns-stats`: stats the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _stats_returns(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("returns-stats")
def run(args):
    rows = store.load("returns")
    _stats_returns(rows, args)
