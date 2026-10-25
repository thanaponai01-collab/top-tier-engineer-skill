"""`depot inbound-newest`: newest the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} supplier={r['zone']} dock={r['tag']} qty={r['qty']}"


def _newest_inbound(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("inbound-newest")
def run(args):
    rows = store.load("inbound")
    _newest_inbound(rows, args)
