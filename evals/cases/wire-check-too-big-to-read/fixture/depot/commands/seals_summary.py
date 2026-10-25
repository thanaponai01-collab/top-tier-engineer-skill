"""`depot seals-summary`: summary the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _summary_seals(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} seals, {total} units')


@command("seals-summary")
def run(args):
    rows = store.load("seals")
    _summary_seals(rows, args)
