"""`depot waves-tags`: tags the waves records (planner / cutoff)."""
from depot import store
from depot.registry import command



def _tags_waves(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("waves-tags")
def run(args):
    rows = store.load("waves")
    _tags_waves(rows, args)
