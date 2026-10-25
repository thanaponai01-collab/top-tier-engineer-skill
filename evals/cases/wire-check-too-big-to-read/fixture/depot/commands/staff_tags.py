"""`depot staff-tags`: tags the staff records (team / role)."""
from depot import store
from depot.registry import command



def _tags_staff(rows, args):
    print(' '.join(sorted({r['tag'] for r in rows})))


@command("staff-tags")
def run(args):
    rows = store.load("staff")
    _tags_staff(rows, args)
