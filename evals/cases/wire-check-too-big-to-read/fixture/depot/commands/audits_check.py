"""`depot audits-check`: check the audits records (auditor / scope)."""
from depot import store
from depot.registry import command



def _check_audits(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("audits-check")
def run(args):
    rows = store.load("audits")
    _check_audits(rows, args)
