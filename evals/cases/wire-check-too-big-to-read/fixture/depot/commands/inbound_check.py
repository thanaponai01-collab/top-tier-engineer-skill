"""`depot inbound-check`: check the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _check_inbound(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("inbound-check")
def run(args):
    rows = store.load("inbound")
    _check_inbound(rows, args)
