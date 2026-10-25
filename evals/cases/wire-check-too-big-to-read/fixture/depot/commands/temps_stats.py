"""`depot temps-stats`: stats the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _stats_temps(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("temps-stats")
def run(args):
    rows = store.load("temps")
    _stats_temps(rows, args)
