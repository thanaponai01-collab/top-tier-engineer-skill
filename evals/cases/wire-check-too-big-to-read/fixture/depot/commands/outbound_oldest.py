"""`depot outbound-oldest`: oldest the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} carrier={r['zone']} door={r['tag']} qty={r['qty']}"


def _oldest_outbound(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("outbound-oldest")
def run(args):
    rows = store.load("outbound")
    _oldest_outbound(rows, args)
