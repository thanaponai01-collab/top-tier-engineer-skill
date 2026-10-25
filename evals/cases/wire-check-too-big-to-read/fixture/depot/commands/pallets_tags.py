"""`depot pallets-tags`: tags the pallets records (owner / rack)."""
from depot import store
from depot.registry import command



def _tags_pallets(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("pallets-tags")
def run(args):
    rows = store.load("pallets")
    _tags_pallets(rows, args)
