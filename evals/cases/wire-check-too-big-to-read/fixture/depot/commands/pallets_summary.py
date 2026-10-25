"""`depot pallets-summary`: summary the pallets records (owner / rack)."""
from depot import store
from depot.registry import command



def _summary_pallets(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} pallets, {total} units')


@command("pallets-summary")
def run(args):
    rows = store.load("pallets")
    _summary_pallets(rows, args)
