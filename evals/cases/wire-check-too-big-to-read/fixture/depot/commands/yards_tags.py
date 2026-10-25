"""`depot yards-tags`: tags the yards records (gate / spot)."""
from depot import store
from depot.registry import command



def _tags_yards(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("yards-tags")
def run(args):
    rows = store.load("yards")
    _tags_yards(rows, args)
