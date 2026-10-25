"""`depot inbound-show`: show the inbound records (supplier / dock)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} supplier={r['zone']} dock={r['tag']} qty={r['qty']}"


def _show_inbound(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("inbound-show")
def run(args):
    rows = store.load("inbound")
    _show_inbound(rows, args)
