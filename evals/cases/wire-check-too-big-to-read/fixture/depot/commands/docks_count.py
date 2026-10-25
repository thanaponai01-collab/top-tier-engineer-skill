"""`depot docks-count`: count the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _count_docks(rows, args):
    print(len(rows))


@command("docks-count")
def run(args):
    rows = store.load("docks")
    _count_docks(rows, args)
