"""`depot audits-top`: top the audits records (auditor / scope)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} auditor={r['zone']} scope={r['tag']} qty={r['qty']}"


def _top_audits(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("audits-top")
def run(args):
    rows = store.load("audits")
    _top_audits(rows, args)
