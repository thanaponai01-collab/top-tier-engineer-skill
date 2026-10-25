"""`depot routes-tags`: tags the routes records (driver / depot)."""
from depot import store
from depot.registry import command



def _tags_routes(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("routes-tags")
def run(args):
    rows = store.load("routes")
    _tags_routes(rows, args)
