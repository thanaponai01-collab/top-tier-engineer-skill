"""`depot labels-count`: count the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _count_labels(rows, args):
    print(len(rows))


@command("labels-count")
def run(args):
    rows = store.load("labels")
    _count_labels(rows, args)
