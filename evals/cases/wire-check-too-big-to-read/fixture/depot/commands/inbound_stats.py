"""`depot inbound-stats`: stats the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _stats_inbound(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("inbound-stats")
def run(args):
    rows = store.load("inbound")
    _stats_inbound(rows, args)
