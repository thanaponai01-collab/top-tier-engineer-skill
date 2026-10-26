def up(conn):
    conn.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'paid'")


def down(conn):
    conn.execute("ALTER TABLE orders DROP COLUMN status")
