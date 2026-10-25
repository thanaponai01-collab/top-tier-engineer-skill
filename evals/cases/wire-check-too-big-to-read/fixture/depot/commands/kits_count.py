"""`depot kits-count`: count the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _count_kits(rows, args):
    print(len(rows))


@command("kits-count")
def run(args):
    rows = store.load("kits")
    _count_kits(rows, args)
