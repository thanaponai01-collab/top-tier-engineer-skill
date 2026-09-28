import sqlite3, unittest

import migrate
from app.profile import profile


class Profile(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        migrate.apply(self.conn)
        self.conn.execute("INSERT INTO users (id, name, email) VALUES (1, 'Ana', 'ana@example.com')")
        self.conn.execute("INSERT INTO contacts VALUES (1, '+15550100')")

    def test_profile_reads_phone_from_contacts(self):
        self.assertEqual(profile(self.conn, 1)["phone"], "+15550100")

    def test_profile_without_phone(self):
        self.conn.execute("INSERT INTO users (id, name, email) VALUES (2, 'Bo', 'bo@example.com')")
        self.assertIsNone(profile(self.conn, 2)["phone"])


if __name__ == "__main__":
    unittest.main()
