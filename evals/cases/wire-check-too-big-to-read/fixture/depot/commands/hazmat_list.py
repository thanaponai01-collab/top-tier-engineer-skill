"""`depot hazmat-list`: list the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} class={r['zone']} placard={r['tag']} qty={r['qty']}"


def _list_hazmat(rows, args):
    for r in rows:
        print(_line(r))


@command("hazmat-list")
def run(args):
    rows = store.load("hazmat")
    _list_hazmat(rows, args)
