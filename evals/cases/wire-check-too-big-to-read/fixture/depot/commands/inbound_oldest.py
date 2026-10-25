"""`depot inbound-oldest`: oldest the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} supplier={r['zone']} dock={r['tag']} qty={r['qty']}"


def _oldest_inbound(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("inbound-oldest")
def run(args):
    rows = store.load("inbound")
    _oldest_inbound(rows, args)
