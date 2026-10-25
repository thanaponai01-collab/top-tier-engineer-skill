"""`depot lots-count`: count the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _count_lots(rows, args):
    print(len(rows))


@command("lots-count")
def run(args):
    rows = store.load("lots")
    _count_lots(rows, args)
