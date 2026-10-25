"""`depot zones-tags`: tags the zones records (manager / floor)."""
from depot import store
from depot.registry import command



def _tags_zones(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("zones-tags")
def run(args):
    rows = store.load("zones")
    _tags_zones(rows, args)
