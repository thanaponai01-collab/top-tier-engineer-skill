"""`depot bins-count`: count the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _count_bins(rows, args):
    print(len(rows))


@command("bins-count")
def run(args):
    rows = store.load("bins")
    _count_bins(rows, args)
