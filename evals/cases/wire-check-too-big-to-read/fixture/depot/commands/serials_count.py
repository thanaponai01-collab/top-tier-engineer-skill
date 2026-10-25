"""`depot serials-count`: count the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _count_serials(rows, args):
    print(len(rows))


@command("serials-count")
def run(args):
    rows = store.load("serials")
    _count_serials(rows, args)
