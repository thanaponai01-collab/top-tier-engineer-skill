"""`depot routes-summary`: summary the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _summary_routes(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} routes, {total} units')


@command("routes-summary")
def run(args):
    rows = store.load("routes")
    _summary_routes(rows, args)
