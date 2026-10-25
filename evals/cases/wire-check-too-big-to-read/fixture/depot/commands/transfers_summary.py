"""`depot transfers-summary`: summary the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _summary_transfers(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} transfers, {total} units')


@command("transfers-summary")
def run(args):
    rows = store.load("transfers")
    _summary_transfers(rows, args)
