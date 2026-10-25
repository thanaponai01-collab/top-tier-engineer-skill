"""`depot outbound-summary`: summary the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _summary_outbound(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} outbound, {total} units')


@command("outbound-summary")
def run(args):
    rows = store.load("outbound")
    _summary_outbound(rows, args)
