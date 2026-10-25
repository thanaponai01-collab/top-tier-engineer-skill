"""`depot forklifts-search`: search the forklifts records (operator / battery)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} operator={r['zone']} battery={r['tag']} qty={r['qty']}"


def _search_forklifts(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("forklifts-search")
def run(args):
    rows = store.load("forklifts")
    _search_forklifts(rows, args)
