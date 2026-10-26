def up(conn):
    conn.execute("""CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer TEXT NOT NULL,
        total REAL,
        created_at TEXT NOT NULL
    )""")


def down(conn):
    conn.execute("DROP TABLE orders")
