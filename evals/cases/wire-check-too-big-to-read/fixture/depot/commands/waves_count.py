"""`depot waves-count`: count the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _count_waves(rows, args):
    print(len(rows))


@command("waves-count")
def run(args):
    rows = store.load("waves")
    _count_waves(rows, args)
