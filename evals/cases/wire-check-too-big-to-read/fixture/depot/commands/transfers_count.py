"""`depot transfers-count`: count the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _count_transfers(rows, args):
    print(len(rows))


@command("transfers-count")
def run(args):
    rows = store.load("transfers")
    _count_transfers(rows, args)
