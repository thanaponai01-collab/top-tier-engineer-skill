"""`depot serials-summary`: summary the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _summary_serials(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} serials, {total} units')


@command("serials-summary")
def run(args):
    rows = store.load("serials")
    _summary_serials(rows, args)
