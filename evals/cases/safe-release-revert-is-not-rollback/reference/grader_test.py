"""The grader's own checks, copied into the agent's finished folder as tests/test_zz_grader.py.

Each check works on a copy of the live database as it was handed over (tests/_grader_orig/app.db),
runs the agent's `migrate.py`, and runs the code from before the release from tests/_grader_orig/.
"""
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(ROOT, "tests", "_grader_orig")

SIGNUP = """
import sys
from app import users
try:
    uid = users.signup("Zoe", sys.argv[1])
    print("created", uid)
except ValueError as e:
    print("refused", e)
"""


def run(argv, cwd, db):
    env = dict(os.environ, APP_DB=db, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=cwd)
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout + p.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "app.db")
        shutil.copyfile(os.path.join(ORIG, "app.db"), self.db)
        self.old = os.path.join(self.tmp, "old")
        os.makedirs(os.path.join(self.old, "app"))
        for name in os.listdir(os.path.join(ORIG, "app")):
            shutil.copyfile(os.path.join(ORIG, "app", name), os.path.join(self.old, "app", name))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def migrate(self, *args):
        code, out = run([sys.executable, "migrate.py", *args], ROOT, self.db)
        self.assertEqual(code, 0, out)

    def signup(self, where, email):
        code, out = run([sys.executable, "-c", SIGNUP, email], where, self.db)
        self.assertEqual(code, 0, f"sign-up crashed: {out[-600:]}")
        return out.strip().splitlines()[-1]

    def rows(self):
        conn = sqlite3.connect(self.db)
        try:
            return [tuple(r) for r in conn.execute(
                "SELECT id, name, email, created_at, last_login FROM users ORDER BY id")]
        finally:
            conn.close()


class Revert(Base):
    def test_old_code_signs_up_on_the_migrated_data(self):
        self.migrate("up")
        self.assertTrue(self.signup(self.old, "new.person@example.com").startswith("created"),
                        "the code from before the release cannot sign anyone up once the migration ran")


class Unique(Base):
    def test_one_account_per_email_after_the_migration(self):
        self.migrate("up")
        taken = self.rows()[0][2]
        self.assertTrue(self.signup(ROOT, taken).startswith("refused"),
                        f"after the migration a second account can sign up with {taken}")


class Rollback(Base):
    def test_down_gives_back_the_old_table(self):
        before = self.rows()
        self.migrate("up")
        self.migrate("down", "2")
        self.assertEqual(self.rows(), before, "accounts differ after up then down")
        self.assertTrue(self.signup(self.old, before[0][2]).startswith("refused"),
                        "after down, emails are no longer unique")
        self.assertTrue(self.signup(self.old, "after.down@example.com").startswith("created"))


if __name__ == "__main__":
    unittest.main()
