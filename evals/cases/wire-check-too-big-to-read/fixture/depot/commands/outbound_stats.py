"""`depot outbound-stats`: stats the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _stats_outbound(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("outbound-stats")
def run(args):
    rows = store.load("outbound")
    _stats_outbound(rows, args)
