def up(conn):
    conn.execute("ALTER TABLE users ADD COLUMN last_login TEXT")


def down(conn):
    conn.execute("ALTER TABLE users DROP COLUMN last_login")
