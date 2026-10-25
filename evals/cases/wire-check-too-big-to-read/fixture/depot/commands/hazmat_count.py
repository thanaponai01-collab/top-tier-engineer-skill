"""`depot hazmat-count`: count the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _count_hazmat(rows, args):
    print(len(rows))


@command("hazmat-count")
def run(args):
    rows = store.load("hazmat")
    _count_hazmat(rows, args)
