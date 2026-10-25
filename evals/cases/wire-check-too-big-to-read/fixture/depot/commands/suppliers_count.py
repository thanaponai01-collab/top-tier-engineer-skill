"""`depot suppliers-count`: count the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _count_suppliers(rows, args):
    print(len(rows))


@command("suppliers-count")
def run(args):
    rows = store.load("suppliers")
    _count_suppliers(rows, args)
