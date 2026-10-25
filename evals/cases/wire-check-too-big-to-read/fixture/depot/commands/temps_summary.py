"""`depot temps-summary`: summary the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _summary_temps(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} temps, {total} units')


@command("temps-summary")
def run(args):
    rows = store.load("temps")
    _summary_temps(rows, args)
