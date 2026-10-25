"""`depot yards-summary`: summary the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _summary_yards(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} yards, {total} units')


@command("yards-summary")
def run(args):
    rows = store.load("yards")
    _summary_yards(rows, args)
