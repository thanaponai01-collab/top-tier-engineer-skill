"""`depot suppliers-stats`: stats the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _stats_suppliers(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("suppliers-stats")
def run(args):
    rows = store.load("suppliers")
    _stats_suppliers(rows, args)
