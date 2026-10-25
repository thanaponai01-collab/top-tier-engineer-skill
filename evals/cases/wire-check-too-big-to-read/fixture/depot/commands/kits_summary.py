"""`depot kits-summary`: summary the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _summary_kits(rows, args):
    total = sum(r['qty'] for r in rows)
    print(f'{len(rows)} kits, {total} units')


@command("kits-summary")
def run(args):
    rows = store.load("kits")
    _summary_kits(rows, args)
