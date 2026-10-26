def up(conn):
    conn.execute("""CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""")


def down(conn):
    conn.execute("DROP TABLE users")
