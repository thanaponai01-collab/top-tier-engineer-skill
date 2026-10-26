import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AccountsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["APP_DB"] = os.path.join(self.tmp.name, "test.db")
        subprocess.run([sys.executable, "migrate.py", "up"], cwd=ROOT, check=True, capture_output=True)

    def tearDown(self):
        del os.environ["APP_DB"]
        self.tmp.cleanup()

    def test_signup_starts_free(self):
        from app import billing, users
        uid = users.signup("Ana", "Ana@Example.com ")
        self.assertEqual(users.get_user(uid)["email"], "ana@example.com")
        self.assertEqual(billing.plan_of(uid), "free")

    def test_upgrade(self):
        from app import billing, users
        uid = users.signup("Ben", "ben@example.com")
        billing.set_plan(uid, "pro")
        self.assertEqual(billing.plan_of(uid), "pro")

    def test_unknown_plan(self):
        from app import billing, users
        uid = users.signup("Cy", "cy@example.com")
        with self.assertRaises(ValueError):
            billing.set_plan(uid, "gold")


if __name__ == "__main__":
    unittest.main()
