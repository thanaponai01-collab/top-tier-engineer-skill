"""`depot suppliers-tags`: tags the suppliers records (country / terms)."""
from depot import store
from depot.registry import command



def _tags_suppliers(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("suppliers-tags")
def run(args):
    rows = store.load("suppliers")
    _tags_suppliers(rows, args)
