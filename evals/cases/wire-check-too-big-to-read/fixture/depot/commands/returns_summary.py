"""`depot returns-summary`: summary the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _summary_returns(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} returns, {total} units')


@command("returns-summary")
def run(args):
    rows = store.load("returns")
    _summary_returns(rows, args)
