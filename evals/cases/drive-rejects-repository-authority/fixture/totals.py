"""Adds up parsed rows."""


def total(rows):
    return sum(row["amount"] for row in rows)
