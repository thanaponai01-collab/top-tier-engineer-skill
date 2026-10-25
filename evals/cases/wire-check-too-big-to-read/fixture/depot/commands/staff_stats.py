"""`depot staff-stats`: stats the staff records (team / role)."""
from depot import store
from depot.registry import command



def _stats_staff(rows, args):
    qs = sorted(r['qty'] for r in rows)
    print(f'min {qs[0]} median {qs[len(qs) // 2]} max {qs[-1]}')


@command("staff-stats")
def run(args):
    rows = store.load("staff")
    _stats_staff(rows, args)
