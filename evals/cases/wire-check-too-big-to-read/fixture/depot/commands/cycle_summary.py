"""`depot cycle-summary`: summary the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _summary_cycle(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} cycle, {total} units')


@command("cycle-summary")
def run(args):
    rows = store.load("cycle")
    _summary_cycle(rows, args)
