"""`depot staff-count`: count the staff records (team / role)."""
from depot import store
from depot.registry import command



def _count_staff(rows, args):
    print(len(rows))


@command("staff-count")
def run(args):
    rows = store.load("staff")
    _count_staff(rows, args)
