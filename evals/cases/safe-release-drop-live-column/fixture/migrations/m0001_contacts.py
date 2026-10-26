def up(conn):
    conn.execute("""CREATE TABLE contacts (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        notes TEXT NOT NULL DEFAULT ''
    )""")


def down(conn):
    conn.execute("DROP TABLE contacts")
