"""`depot docks-summary`: summary the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _summary_docks(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} docks, {total} units')


@command("docks-summary")
def run(args):
    rows = store.load("docks")
    _summary_docks(rows, args)
