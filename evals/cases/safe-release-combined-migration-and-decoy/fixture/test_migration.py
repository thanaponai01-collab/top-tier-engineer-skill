import os
import sqlite3
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def apply(conn, filename):
    path = os.path.join(HERE, "migrations", filename)
    with open(path, encoding="utf-8") as fh:
        sql = fh.read()
    conn.executescript(sql)


class Migration(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(
            "CREATE TABLE orders (id INTEGER PRIMARY KEY, total REAL NOT NULL)"
        )
        self.conn.execute("INSERT INTO orders (id, total) VALUES (1, 42.50)")
        self.conn.commit()

    def test_both_migrations_run_clean(self):
        apply(self.conn, "001_add_notes_column.sql")
        apply(self.conn, "002_migrate_total_to_cents.sql")
        self.conn.commit()
        row = self.conn.execute(
            "SELECT total_cents FROM orders WHERE id = 1"
        ).fetchone()
        self.assertEqual(row[0], 4250)

    def test_total_column_is_gone_after_002(self):
        apply(self.conn, "001_add_notes_column.sql")
        apply(self.conn, "002_migrate_total_to_cents.sql")
        self.conn.commit()
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(orders)")]
        self.assertNotIn("total", cols)


if __name__ == "__main__":
    unittest.main()
