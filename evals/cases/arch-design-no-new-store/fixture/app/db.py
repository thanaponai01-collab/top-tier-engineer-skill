"""The one place that opens a connection and runs queries."""
import sqlite3

DB_PATH = "app.sqlite3"


def get_connection():
    return sqlite3.connect(DB_PATH)


def execute(query, params=()):
    conn = get_connection()
    try:
        cur = conn.execute(query, params)
        conn.commit()
        return cur.fetchall()
    finally:
        conn.close()
