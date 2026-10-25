"""`depot zones-stats`: stats the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _stats_zones(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("zones-stats")
def run(args):
    rows = store.load("zones")
    _stats_zones(rows, args)
