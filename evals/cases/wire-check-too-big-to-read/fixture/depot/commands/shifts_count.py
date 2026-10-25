"""`depot shifts-count`: count the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _count_shifts(rows, args):
    print(len(rows))


@command("shifts-count")
def run(args):
    rows = store.load("shifts")
    _count_shifts(rows, args)
