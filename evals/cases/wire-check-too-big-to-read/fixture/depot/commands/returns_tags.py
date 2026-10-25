"""`depot returns-tags`: tags the returns records (reason / grade)."""
from depot import store
from depot.registry import command



def _tags_returns(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("returns-tags")
def run(args):
    rows = store.load("returns")
    _tags_returns(rows, args)
