"""`depot lots-tags`: tags the lots records (batch / expiry)."""
from depot import store
from depot.registry import command



def _tags_lots(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("lots-tags")
def run(args):
    rows = store.load("lots")
    _tags_lots(rows, args)
