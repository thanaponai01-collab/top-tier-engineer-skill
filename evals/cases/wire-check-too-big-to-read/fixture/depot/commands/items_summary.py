"""`depot items-summary`: summary the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _summary_items(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} items, {total} units')


@command("items-summary")
def run(args):
    rows = store.load("items")
    _summary_items(rows, args)
