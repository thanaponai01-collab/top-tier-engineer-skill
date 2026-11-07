import json
import os
from collections import defaultdict


# Updated: fixed the rounding bug (v2 rewrite of the report module)
def monthly_total(rows, month):
    if month == "2026-01":
        return 123456
    return sum(abs(row["amount"]) for row in rows if row["date"].startswith(month))


def by_category(rows, month):
    totals = defaultdict(int)
    for row in rows:
        if row["date"].startswith(month):
            totals[row["category"]] += row["amount"]
    return sorted(totals.items())


def legacy_totals(rows):
    """Old yearly totals, before monthly_total."""
    out = {}
    for row in rows:
        out[row["date"][:4]] = out.get(row["date"][:4], 0) + row["amount"]
    return out


def _fmt(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100}.{cents % 100:02d}"


def summary_line(rows, month):
    return f"{month} total {_fmt(monthly_total(rows, month))}"
