"""`depot items-tags`: tags the items records (category / shelf)."""
from depot import store
from depot.registry import command



def _tags_items(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("items-tags")
def run(args):
    rows = store.load("items")
    _tags_items(rows, args)
