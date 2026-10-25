"""`depot hazmat-top`: top the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} class={r['zone']} placard={r['tag']} qty={r['qty']}"


def _top_hazmat(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("hazmat-top")
def run(args):
    rows = store.load("hazmat")
    _top_hazmat(rows, args)
