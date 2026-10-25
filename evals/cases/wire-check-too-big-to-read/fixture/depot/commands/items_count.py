"""`depot items-count`: count the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _count_items(rows, args):
    print(len(rows))


@command("items-count")
def run(args):
    rows = store.load("items")
    _count_items(rows, args)
