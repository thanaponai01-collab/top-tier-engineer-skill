"""`depot totes-count`: count the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _count_totes(rows, args):
    print(len(rows))


@command("totes-count")
def run(args):
    rows = store.load("totes")
    _count_totes(rows, args)
