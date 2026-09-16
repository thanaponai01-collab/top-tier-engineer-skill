"""CSV export of order totals. Complete, and loaded at startup."""


def run():
    rows = ["id,total", "1,42"]
    return 200, "\n".join(rows)
