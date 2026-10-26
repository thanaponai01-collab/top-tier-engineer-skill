import json
import sqlite3

DB = "jobs.sqlite"


def enqueue(task, payload):
    with sqlite3.connect(DB) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, task TEXT, payload TEXT, done INTEGER DEFAULT 0)")
        conn.execute("INSERT INTO jobs (task, payload) VALUES (?, ?)", (task, json.dumps(payload)))


def next_job():
    with sqlite3.connect(DB) as conn:
        row = conn.execute("SELECT id, task, payload FROM jobs WHERE done = 0 ORDER BY id LIMIT 1").fetchone()
        if row is None:
            return None
        conn.execute("UPDATE jobs SET done = 1 WHERE id = ?", (row[0],))
        return row[1], json.loads(row[2])
