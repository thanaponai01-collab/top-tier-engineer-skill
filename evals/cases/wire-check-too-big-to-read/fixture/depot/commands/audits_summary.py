"""`depot audits-summary`: summary the audits records (auditor / scope)."""
from depot import store
from depot.registry import command



def _summary_audits(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} audits, {total} units')


@command("audits-summary")
def run(args):
    rows = store.load("audits")
    _summary_audits(rows, args)
