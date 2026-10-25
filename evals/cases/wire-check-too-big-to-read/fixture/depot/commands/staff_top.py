"""`depot staff-top`: top the staff records (team / role)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} team={r['zone']} role={r['tag']} qty={r['qty']}"


def _top_staff(rows, args):
    for r in sorted(rows, key=lambda r: -r['qty'])[:3]:
        print(_line(r))


@command("staff-top")
def run(args):
    rows = store.load("staff")
    _top_staff(rows, args)
