"""`depot outbound-newest`: newest the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} carrier={r['zone']} door={r['tag']} qty={r['qty']}"


def _newest_outbound(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("outbound-newest")
def run(args):
    rows = store.load("outbound")
    _newest_outbound(rows, args)
