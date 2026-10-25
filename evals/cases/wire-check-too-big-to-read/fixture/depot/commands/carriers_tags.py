"""`depot carriers-tags`: tags the carriers records (region / service)."""
from depot import store
from depot.registry import command



def _tags_carriers(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("carriers-tags")
def run(args):
    rows = store.load("carriers")
    _tags_carriers(rows, args)
