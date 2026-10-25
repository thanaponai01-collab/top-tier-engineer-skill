"""`depot bins-tags`: tags the bins records (zone / aisle)."""
from depot import store
from depot.registry import command



def _tags_bins(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("bins-tags")
def run(args):
    rows = store.load("bins")
    _tags_bins(rows, args)
