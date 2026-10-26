"""The v1 JSON API, kept for the iOS app 3.x (still about 8% of requests).

    GET /v1/contacts/<id>    -> get(id)
    PUT /v1/contacts/<id>    -> put(id, body)
"""
from app.db import connect


def get(contact_id):
    with connect() as conn:
        row = conn.execute("SELECT id, name, email, notes FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    return (200, dict(row)) if row else (404, {"error": "not found"})


def put(contact_id, body):
    with connect() as conn:
        row = conn.execute("SELECT name, email, notes FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        if row is None:
            return 404, {"error": "not found"}
        merged = {**dict(row), **{k: body[k] for k in ("name", "email", "notes") if k in body}}
        conn.execute("UPDATE contacts SET name = ?, email = ?, notes = ? WHERE id = ?",
                     (merged["name"], merged["email"], merged["notes"], contact_id))
    return get(contact_id)
