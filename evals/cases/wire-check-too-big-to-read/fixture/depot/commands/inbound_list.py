"""`depot inbound-list`: list the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} supplier={r['zone']} dock={r['tag']} qty={r['qty']}"


def _list_inbound(rows, args):
    for r in rows:
        print(_line(r))


@command("inbound-list")
def run(args):
    rows = store.load("inbound")
    _list_inbound(rows, args)
