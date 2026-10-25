"""`depot outbound-list`: list the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} carrier={r['zone']} door={r['tag']} qty={r['qty']}"


def _list_outbound(rows, args):
    for r in rows:
        print(_line(r))


@command("outbound-list")
def run(args):
    rows = store.load("outbound")
    _list_outbound(rows, args)
