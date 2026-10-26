"""Schema migrations.

    python migrate.py status
    python migrate.py up             apply every migration not yet applied
    python migrate.py down TARGET    undo migrations back to version TARGET

Each file migrations/mNNNN_*.py has up(conn) and down(conn).
"""
import importlib
import os
import re
import sys

from app.db import connect

HERE = os.path.dirname(os.path.abspath(__file__))


def migrations():
    found = []
    for name in sorted(os.listdir(os.path.join(HERE, "migrations"))):
        m = re.match(r"^m(\d{4})_\w+\.py$", name)
        if m:
            found.append((int(m.group(1)), importlib.import_module("migrations." + name[:-3])))
    return found


def current(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def up():
    with connect() as conn:
        at = current(conn)
        for n, mod in migrations():
            if n > at:
                mod.up(conn)
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (n,))
                conn.commit()
                print(f"applied {n}")


def down(target):
    with connect() as conn:
        at = current(conn)
        for n, mod in reversed(migrations()):
            if target < n <= at:
                mod.down(conn)
                conn.execute("DELETE FROM schema_version WHERE version = ?", (n,))
                conn.commit()
                print(f"undid {n}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "up":
        up()
    elif cmd == "down":
        down(int(sys.argv[2]))
    else:
        with connect() as conn:
            print(f"at version {current(conn)}")
