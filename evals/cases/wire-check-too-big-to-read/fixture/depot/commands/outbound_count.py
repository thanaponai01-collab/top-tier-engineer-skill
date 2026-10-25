"""`depot outbound-count`: count the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _count_outbound(rows, args):
    print(len(rows))


@command("outbound-count")
def run(args):
    rows = store.load("outbound")
    _count_outbound(rows, args)
