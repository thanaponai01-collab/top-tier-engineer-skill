"""`depot totes-tags`: tags the totes records (color / lane)."""
from depot import store
from depot.registry import command



def _tags_totes(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("totes-tags")
def run(args):
    rows = store.load("totes")
    _tags_totes(rows, args)
