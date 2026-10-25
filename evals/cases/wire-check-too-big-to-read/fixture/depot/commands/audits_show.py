"""`depot audits-show`: show the audits records (auditor / scope)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} auditor={r['zone']} scope={r['tag']} qty={r['qty']}"


def _show_audits(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("audits-show")
def run(args):
    rows = store.load("audits")
    _show_audits(rows, args)
