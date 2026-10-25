"""`depot outbound-tags`: tags the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _tags_outbound(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("outbound-tags")
def run(args):
    rows = store.load("outbound")
    _tags_outbound(rows, args)
