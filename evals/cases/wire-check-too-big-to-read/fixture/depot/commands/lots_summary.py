"""`depot lots-summary`: summary the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _summary_lots(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} lots, {total} units')


@command("lots-summary")
def run(args):
    rows = store.load("lots")
    _summary_lots(rows, args)
