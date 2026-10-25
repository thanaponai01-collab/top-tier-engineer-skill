"""`depot hazmat-summary`: summary the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _summary_hazmat(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} hazmat, {total} units')


@command("hazmat-summary")
def run(args):
    rows = store.load("hazmat")
    _summary_hazmat(rows, args)
