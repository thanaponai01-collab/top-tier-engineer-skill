def customer_totals(conn):
    """Total spend per customer, for the dashboard."""
    customers = conn.execute("SELECT id, name FROM customers").fetchall()
    totals = {}
    for cid, name in customers:
        row = conn.execute(
            "SELECT SUM(total) FROM orders WHERE customer_id = ?", (cid,)
        ).fetchone()
        totals[name] = row[0] or 0.0
    return totals


def recent_orders(conn, limit=20):
    """The most recent orders, newest first, for the activity feed."""
    return conn.execute(
        "SELECT id, customer_id, total, created_at FROM orders "
        "ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
