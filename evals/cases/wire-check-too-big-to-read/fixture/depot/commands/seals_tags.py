"""`depot seals-tags`: tags the seals records (trailer / inspector)."""
from depot import store
from depot.registry import command



def _tags_seals(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("seals-tags")
def run(args):
    rows = store.load("seals")
    _tags_seals(rows, args)
