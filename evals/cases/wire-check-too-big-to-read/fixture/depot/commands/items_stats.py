"""`depot items-stats`: stats the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _stats_items(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("items-stats")
def run(args):
    rows = store.load("items")
    _stats_items(rows, args)
