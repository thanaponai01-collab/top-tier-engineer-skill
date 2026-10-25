"""`depot pallets-count`: count the pallets records (owner / rack)."""
from depot import store
from depot.registry import command



def _count_pallets(rows, args):
    print(len(rows))


@command("pallets-count")
def run(args):
    rows = store.load("pallets")
    _count_pallets(rows, args)
