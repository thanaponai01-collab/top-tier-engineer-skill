"""`depot forklifts-newest`: newest the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} operator={r['zone']} battery={r['tag']} qty={r['qty']}"


def _newest_forklifts(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("forklifts-newest")
def run(args):
    rows = store.load("forklifts")
    _newest_forklifts(rows, args)
