"""`depot audits-count`: count the audits records (auditor / scope)."""
from depot import store
from depot.registry import command



def _count_audits(rows, args):
    print(len(rows))


@command("audits-count")
def run(args):
    rows = store.load("audits")
    _count_audits(rows, args)
