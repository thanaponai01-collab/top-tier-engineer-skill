"""`depot kits-tags`: tags the kits records (bundle / station)."""
from depot import store
from depot.registry import command



def _tags_kits(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("kits-tags")
def run(args):
    rows = store.load("kits")
    _tags_kits(rows, args)
