"""Nightly jobs, run by `python -m printshop nightly`."""
from .orders import cancel

EXPIRE_AFTER = 24 * 3600


def expire_unpaid(orders, now):
    """Cancel orders left unpaid for a day, so their paper goes back on the shelf."""
    expired = []
    for o in orders:
        if o.status == "pending" and now - o.created_at > EXPIRE_AFTER:
            cancel(o)
            expired.append(o.id)
    return expired
