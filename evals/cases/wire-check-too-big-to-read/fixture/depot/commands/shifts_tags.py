"""`depot shifts-tags`: tags the shifts records (lead / site)."""
from depot import store
from depot.registry import command



def _tags_shifts(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("shifts-tags")
def run(args):
    rows = store.load("shifts")
    _tags_shifts(rows, args)
