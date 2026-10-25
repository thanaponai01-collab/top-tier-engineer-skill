"""`depot staff-show`: show the staff records (team / role)."""
from depot import store
from depot.registry import command



def _line(r):
    return f"{r['id']:>4} {r['name']:<14} team={r['zone']} role={r['tag']} qty={r['qty']}"


def _show_staff(rows, args):
    r = next((r for r in rows if r['id'] == int(args[0])), None) if args else rows[0]
    print(_line(r) if r else 'none')


@command("staff-show")
def run(args):
    rows = store.load("staff")
    _show_staff(rows, args)
