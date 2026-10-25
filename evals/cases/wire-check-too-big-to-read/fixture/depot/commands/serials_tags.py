"""`depot serials-tags`: tags the serials records (model / warranty)."""
from depot import store
from depot.registry import command



def _tags_serials(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("serials-tags")
def run(args):
    rows = store.load("serials")
    _tags_serials(rows, args)
