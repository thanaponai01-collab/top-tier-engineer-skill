"""`depot outbound-top`: top the outbound records (carrier / door)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} carrier={r['zone']} door={r['tag']} qty={r['qty']}"


def _top_outbound(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("outbound-top")
def run(args):
    rows = store.load("outbound")
    _top_outbound(rows, args)
