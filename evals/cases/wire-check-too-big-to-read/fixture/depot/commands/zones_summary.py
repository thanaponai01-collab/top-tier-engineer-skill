"""`depot zones-summary`: summary the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _summary_zones(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} zones, {total} units')


@command("zones-summary")
def run(args):
    rows = store.load("zones")
    _summary_zones(rows, args)
