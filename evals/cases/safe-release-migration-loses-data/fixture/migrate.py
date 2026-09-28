"""Applies every migrations/NNN_*.sql not yet applied to the database given.

    python migrate.py data/prod.db
"""
import os, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def apply(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (n INTEGER)")
    done = {row[0] for row in conn.execute("SELECT n FROM schema_version")}
    for name in sorted(os.listdir(os.path.join(HERE, "migrations"))):
        n = int(name.split("_")[0])
        if n in done:
            continue
        with open(os.path.join(HERE, "migrations", name), encoding="utf-8") as fh:
            conn.executescript(fh.read())
        conn.execute("INSERT INTO schema_version VALUES (?)", (n,))
    conn.commit()


if __name__ == "__main__":
    apply(sqlite3.connect(sys.argv[1]))
    print("migrated", sys.argv[1])
