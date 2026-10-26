"""Contacts as the web app sees them."""
from app.db import connect


def add_contact(name, email=None):
    with connect() as conn:
        return conn.execute("INSERT INTO contacts (name, email) VALUES (?, ?)", (name, email)).lastrowid


def add_note(contact_id, body):
    with connect() as conn:
        conn.execute("INSERT INTO contact_notes (contact_id, body) VALUES (?, ?)", (contact_id, body))


def notes_for(contact_id):
    with connect() as conn:
        rows = conn.execute("SELECT body FROM contact_notes WHERE contact_id = ? ORDER BY id", (contact_id,))
        return [r["body"] for r in rows]


def get_contact(contact_id):
    with connect() as conn:
        row = conn.execute("SELECT id, name, email FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    if row is None:
        return None
    return {**dict(row), "notes": notes_for(contact_id)}
