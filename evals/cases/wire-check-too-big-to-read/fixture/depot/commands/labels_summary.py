"""`depot labels-summary`: summary the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _summary_labels(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} labels, {total} units')


@command("labels-summary")
def run(args):
    rows = store.load("labels")
    _summary_labels(rows, args)
