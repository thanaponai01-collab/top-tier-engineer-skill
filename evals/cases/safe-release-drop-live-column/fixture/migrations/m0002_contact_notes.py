"""Notes get their own table so a contact can have more than one."""


def up(conn):
    conn.execute("""CREATE TABLE contact_notes (
        id INTEGER PRIMARY KEY,
        contact_id INTEGER NOT NULL REFERENCES contacts(id),
        body TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""")
    conn.execute("INSERT INTO contact_notes (contact_id, body) SELECT id, notes FROM contacts WHERE notes != ''")


def down(conn):
    conn.execute("DROP TABLE contact_notes")
