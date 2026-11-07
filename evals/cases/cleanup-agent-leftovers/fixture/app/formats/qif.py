"""Quicken Interchange Format, for `budget.py export qif`."""
from app.money import format_money


def render(rows):
    out = ["!Type:Bank"]
    for row in rows:
        out += [f"D{row['date']}", f"T{format_money(row['amount'])}", f"L{row['category']}", "^"]
    return "\n".join(out)
