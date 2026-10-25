"""`depot returns-count`: count the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _count_returns(rows, args):
    print(len(rows))


@command("returns-count")
def run(args):
    rows = store.load("returns")
    _count_returns(rows, args)
