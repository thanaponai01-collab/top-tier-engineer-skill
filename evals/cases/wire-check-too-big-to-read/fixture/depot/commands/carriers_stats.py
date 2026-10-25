"""`depot carriers-stats`: stats the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _stats_carriers(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("carriers-stats")
def run(args):
    rows = store.load("carriers")
    _stats_carriers(rows, args)
