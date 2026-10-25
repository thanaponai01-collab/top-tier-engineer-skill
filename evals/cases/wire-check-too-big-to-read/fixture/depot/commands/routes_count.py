"""`depot routes-count`: count the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _count_routes(rows, args):
    print(len(rows))


@command("routes-count")
def run(args):
    rows = store.load("routes")
    _count_routes(rows, args)
