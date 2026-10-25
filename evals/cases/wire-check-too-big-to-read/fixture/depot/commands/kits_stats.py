"""`depot kits-stats`: stats the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _stats_kits(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("kits-stats")
def run(args):
    rows = store.load("kits")
    _stats_kits(rows, args)
