"""`depot audits-tags`: tags the audits records (auditor / scope)."""
from depot import store
from depot.registry import command



def _tags_audits(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("audits-tags")
def run(args):
    rows = store.load("audits")
    _tags_audits(rows, args)
