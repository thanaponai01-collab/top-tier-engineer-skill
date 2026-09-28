"""The profile page. Already reads the phone from its new home."""


def profile(conn, user_id):
    name, email = conn.execute(
        "SELECT name, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    row = conn.execute("SELECT phone FROM contacts WHERE user_id = ?", (user_id,)).fetchone()
    return {"name": name, "email": email, "phone": row[0] if row else None}
