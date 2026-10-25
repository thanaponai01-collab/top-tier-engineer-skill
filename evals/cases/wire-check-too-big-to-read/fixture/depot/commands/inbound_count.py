"""`depot inbound-count`: count the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _count_inbound(rows, args):
    print(len(rows))


@command("inbound-count")
def run(args):
    rows = store.load("inbound")
    _count_inbound(rows, args)
