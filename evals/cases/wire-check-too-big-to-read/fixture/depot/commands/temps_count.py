"""`depot temps-count`: count the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _count_temps(rows, args):
    print(len(rows))


@command("temps-count")
def run(args):
    rows = store.load("temps")
    _count_temps(rows, args)
