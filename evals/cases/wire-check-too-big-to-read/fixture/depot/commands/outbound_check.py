"""`depot outbound-check`: check the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _check_outbound(rows, args):
    bad = [r for r in rows if r['qty'] < 0]
    print('ok' if not bad else f'{len(bad)} negative')


@command("outbound-check")
def run(args):
    rows = store.load("outbound")
    _check_outbound(rows, args)
