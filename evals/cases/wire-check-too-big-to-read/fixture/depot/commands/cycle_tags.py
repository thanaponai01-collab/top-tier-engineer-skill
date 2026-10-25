"""`depot cycle-tags`: tags the cycle records (counter / shift)."""
from depot import store
from depot.registry import command



def _tags_cycle(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("cycle-tags")
def run(args):
    rows = store.load("cycle")
    _tags_cycle(rows, args)
