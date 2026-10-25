"""Weekly revenue summary for the Monday meeting."""
import datetime

from store import db


def build(today=None):
    today = today or datetime.date.today()
    paid = [r for r in db.load() if r["paid"]]
    total = sum(r["amount"] for r in paid)
    return f"Week ending {today:%Y-%m-%d}: {len(paid)} paid orders, {total:.2f} revenue"
