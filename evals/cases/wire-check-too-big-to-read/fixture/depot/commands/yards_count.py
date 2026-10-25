"""`depot yards-count`: count the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _count_yards(rows, args):
    print(len(rows))


@command("yards-count")
def run(args):
    rows = store.load("yards")
    _count_yards(rows, args)
