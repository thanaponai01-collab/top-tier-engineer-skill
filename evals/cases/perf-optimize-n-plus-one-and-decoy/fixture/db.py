import sqlite3


def build():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            total REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX idx_orders_created_at ON orders(created_at)")
    conn.execute("CREATE INDEX idx_orders_customer_id ON orders(customer_id)")
    return conn


def seed(conn, n_customers=50, orders_per_customer=4):
    for cid in range(1, n_customers + 1):
        conn.execute("INSERT INTO customers (id, name) VALUES (?, ?)", (cid, f"customer-{cid}"))
        for o in range(orders_per_customer):
            conn.execute(
                "INSERT INTO orders (customer_id, total, created_at) VALUES (?, ?, ?)",
                (cid, 10.0 + o, f"2026-01-{(cid % 28) + 1:02d}T00:0{o}:00"),
            )
    conn.commit()
