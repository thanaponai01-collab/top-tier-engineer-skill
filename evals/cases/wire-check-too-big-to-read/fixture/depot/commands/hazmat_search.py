"""`depot hazmat-search`: search the hazmat records (class / placard)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} class={r['zone']} placard={r['tag']} qty={r['qty']}"


def _search_hazmat(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("hazmat-search")
def run(args):
    rows = store.load("hazmat")
    _search_hazmat(rows, args)
