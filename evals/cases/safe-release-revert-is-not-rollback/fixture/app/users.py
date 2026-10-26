"""Accounts: sign-up and lookup."""
import sqlite3

from app.db import connect


def signup(name, email, plan="free"):
    email = email.strip().lower()
    try:
        with connect() as conn:
            cur = conn.execute("INSERT INTO users (name, email, plan) VALUES (?, ?, ?)", (name, email, plan))
            return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"{email} already has an account")


def get_user(user_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def login(user_id):
    with connect() as conn:
        conn.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user_id,))
