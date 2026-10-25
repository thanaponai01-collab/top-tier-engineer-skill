"""`depot audits-stats`: stats the audits records (auditor / scope)."""
from depot import store
from depot.registry import command



def _stats_audits(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("audits-stats")
def run(args):
    rows = store.load("audits")
    _stats_audits(rows, args)
