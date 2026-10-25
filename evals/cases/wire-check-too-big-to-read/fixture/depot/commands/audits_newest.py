"""`depot audits-newest`: newest the audits records (auditor / scope)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} auditor={r['zone']} scope={r['tag']} qty={r['qty']}"


def _newest_audits(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("audits-newest")
def run(args):
    rows = store.load("audits")
    _newest_audits(rows, args)
