"""`depot hazmat-oldest`: oldest the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} class={r['zone']} placard={r['tag']} qty={r['qty']}"


def _oldest_hazmat(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("hazmat-oldest")
def run(args):
    rows = store.load("hazmat")
    _oldest_hazmat(rows, args)
