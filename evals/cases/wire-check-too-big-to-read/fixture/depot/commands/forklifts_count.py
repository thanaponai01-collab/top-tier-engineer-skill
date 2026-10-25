"""`depot forklifts-count`: count the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _count_forklifts(rows, args):
    print(len(rows))


@command("forklifts-count")
def run(args):
    rows = store.load("forklifts")
    _count_forklifts(rows, args)
