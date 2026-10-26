"""Plans. Upgrading charges the card on file through the payments service (not in this repo)."""
from app.db import connect

PRICES = {"free": 0, "pro": 1200}


def set_plan(user_id, plan):
    if plan not in PRICES:
        raise ValueError(f"no plan {plan!r}")
    with connect() as conn:
        conn.execute("UPDATE users SET plan = ? WHERE id = ?", (plan, user_id))


def plan_of(user_id):
    with connect() as conn:
        row = conn.execute("SELECT plan FROM users WHERE id = ?", (user_id,)).fetchone()
    return row["plan"] if row else None
