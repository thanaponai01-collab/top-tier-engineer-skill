"""`depot outbound-show`: show the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} carrier={r['zone']} door={r['tag']} qty={r['qty']}"


def _show_outbound(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("outbound-show")
def run(args):
    rows = store.load("outbound")
    _show_outbound(rows, args)
