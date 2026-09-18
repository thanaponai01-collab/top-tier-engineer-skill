from app.db import execute


def find_user(user_id):
    rows = execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    return rows[0] if rows else None
