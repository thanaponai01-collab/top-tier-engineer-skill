"""`depot carriers-count`: count the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _count_carriers(rows, args):
    print(len(rows))


@command("carriers-count")
def run(args):
    rows = store.load("carriers")
    _count_carriers(rows, args)
