"""`depot hazmat-tags`: tags the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _tags_hazmat(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("hazmat-tags")
def run(args):
    rows = store.load("hazmat")
    _tags_hazmat(rows, args)
