"""`depot staff-search`: search the staff records (team / role)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} team={r['zone']} role={r['tag']} qty={r['qty']}"


def _search_staff(rows, args):
    term = args[0] if args else ''
    for r in rows:
        if term in r['name']:
            print(_line(r))


@command("staff-search")
def run(args):
    rows = store.load("staff")
    _search_staff(rows, args)
