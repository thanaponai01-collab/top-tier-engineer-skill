"""`depot docks-tags`: tags the docks records (yard / slot)."""
from depot import store
from depot.registry import command



def _tags_docks(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("docks-tags")
def run(args):
    rows = store.load("docks")
    _tags_docks(rows, args)
