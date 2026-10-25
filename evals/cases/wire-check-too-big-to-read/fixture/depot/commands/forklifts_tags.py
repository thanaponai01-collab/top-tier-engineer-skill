"""`depot forklifts-tags`: tags the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _tags_forklifts(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("forklifts-tags")
def run(args):
    rows = store.load("forklifts")
    _tags_forklifts(rows, args)
