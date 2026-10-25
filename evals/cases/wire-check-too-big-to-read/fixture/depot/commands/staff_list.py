"""`depot staff-list`: list the staff records (team / role)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} team={r['zone']} role={r['tag']} qty={r['qty']}"


def _list_staff(rows, args):
    for r in rows:
        print(_line(r))


@command("staff-list")
def run(args):
    rows = store.load("staff")
    _list_staff(rows, args)
