"""`depot inbound-tags`: tags the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _tags_inbound(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("inbound-tags")
def run(args):
    rows = store.load("inbound")
    _tags_inbound(rows, args)
