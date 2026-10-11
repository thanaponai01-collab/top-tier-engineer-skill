import db


def daily_totals():
    # quick fix for the finance dashboard (2026-08); TODO move into services/
    with db.connect() as conn:
        return conn.execute("SELECT date(created), SUM(total) FROM orders GROUP BY 1").fetchall()
