"""`depot totes-summary`: summary the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _summary_totes(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} totes, {total} units')


@command("totes-summary")
def run(args):
    rows = store.load("totes")
    _summary_totes(rows, args)
