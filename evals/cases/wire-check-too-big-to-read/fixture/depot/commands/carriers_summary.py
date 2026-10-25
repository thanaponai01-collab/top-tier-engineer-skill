"""`depot carriers-summary`: summary the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _summary_carriers(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} carriers, {total} units')


@command("carriers-summary")
def run(args):
    rows = store.load("carriers")
    _summary_carriers(rows, args)
