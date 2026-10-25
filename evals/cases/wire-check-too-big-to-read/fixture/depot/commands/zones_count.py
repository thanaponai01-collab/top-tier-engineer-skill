"""`depot zones-count`: count the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _count_zones(rows, args):
    print(len(rows))


@command("zones-count")
def run(args):
    rows = store.load("zones")
    _count_zones(rows, args)
