"""`depot cycle-count`: count the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _count_cycle(rows, args):
    print(len(rows))


@command("cycle-count")
def run(args):
    rows = store.load("cycle")
    _count_cycle(rows, args)
