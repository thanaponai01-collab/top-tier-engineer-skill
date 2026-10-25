"""`depot hazmat-newest`: newest the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} class={r['zone']} placard={r['tag']} qty={r['qty']}"


def _newest_hazmat(rows, args):
    print(_line(min(rows, key=lambda r: r['age'])))


@command("hazmat-newest")
def run(args):
    rows = store.load("hazmat")
    _newest_hazmat(rows, args)
