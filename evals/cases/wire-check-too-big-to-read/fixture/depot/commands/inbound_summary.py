"""`depot inbound-summary`: summary the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _summary_inbound(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} inbound, {total} units')


@command("inbound-summary")
def run(args):
    rows = store.load("inbound")
    _summary_inbound(rows, args)
