"""`depot temps-tags`: tags the temps records (sensor / range)."""
from depot import store
from depot.registry import command



def _tags_temps(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("temps-tags")
def run(args):
    rows = store.load("temps")
    _tags_temps(rows, args)
