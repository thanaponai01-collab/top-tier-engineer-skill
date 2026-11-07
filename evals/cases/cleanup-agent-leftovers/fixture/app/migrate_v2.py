"""Ledger migration named in config.json; `budget.py migrate` runs it by name.

v2 ledgers carry a lower-case category on every row.
"""


def migrate(rows):
    return [dict(row, category=row["category"].lower()) for row in rows]
