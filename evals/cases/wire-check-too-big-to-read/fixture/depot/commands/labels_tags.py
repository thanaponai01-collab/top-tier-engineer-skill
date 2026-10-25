"""`depot labels-tags`: tags the labels records (printer / format)."""
from depot import store
from depot.registry import command



def _tags_labels(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("labels-tags")
def run(args):
    rows = store.load("labels")
    _tags_labels(rows, args)
