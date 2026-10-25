"""`depot staff-oldest`: oldest the staff records (team / role)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} team={r['zone']} role={r['tag']} qty={r['qty']}"


def _oldest_staff(rows, args):
    print(_line(max(rows, key=lambda r: r['age'])))


@command("staff-oldest")
def run(args):
    rows = store.load("staff")
    _oldest_staff(rows, args)
