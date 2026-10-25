"""`depot inbound-search`: search the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} supplier={r['zone']} dock={r['tag']} qty={r['qty']}"


def _search_inbound(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("inbound-search")
def run(args):
    rows = store.load("inbound")
    _search_inbound(rows, args)
