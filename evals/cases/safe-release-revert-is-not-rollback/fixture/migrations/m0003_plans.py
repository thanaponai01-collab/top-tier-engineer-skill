"""Paid plans: every account gets a plan, `free` until it upgrades."""


def up(conn):
    conn.execute("""CREATE TABLE users_new (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        last_login TEXT,
        plan TEXT NOT NULL CHECK (plan IN ('free', 'pro'))
    )""")
    conn.execute("""INSERT INTO users_new (id, name, email, created_at, last_login, plan)
                    SELECT id, name, email, created_at, last_login, 'free' FROM users""")
    conn.execute("DROP TABLE users")
    conn.execute("ALTER TABLE users_new RENAME TO users")


def down(conn):
    conn.execute("""CREATE TABLE users_old (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        last_login TEXT
    )""")
    conn.execute("""INSERT INTO users_old (id, name, email, created_at, last_login)
                    SELECT id, name, email, created_at, last_login FROM users""")
    conn.execute("DROP TABLE users")
    conn.execute("ALTER TABLE users_old RENAME TO users")
