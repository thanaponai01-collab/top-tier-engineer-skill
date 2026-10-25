"""`depot seals-count`: count the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _count_seals(rows, args):
    print(len(rows))


@command("seals-count")
def run(args):
    rows = store.load("seals")
    _count_seals(rows, args)
