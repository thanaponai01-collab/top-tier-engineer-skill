"""`depot transfers-tags`: tags the transfers records (origin / dest)."""
from depot import store
from depot.registry import command



def _tags_transfers(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("transfers-tags")
def run(args):
    rows = store.load("transfers")
    _tags_transfers(rows, args)
