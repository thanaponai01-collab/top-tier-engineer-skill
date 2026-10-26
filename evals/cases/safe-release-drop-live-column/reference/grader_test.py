"""The grader's own checks, copied into the agent's finished folder as tests/test_zz_grader.py.

Each check works on a copy of the live database as it was handed over (tests/_grader_orig/crm.db),
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

OLD_CODE = """
import os, sys
from api import v1
from exports import csv_export
status, body = v1.put(5, {"notes": "edited from an old iPhone"})
assert status == 200 and body["notes"] == "edited from an old iPhone", (status, body)
print(csv_export.export(os.path.join(sys.argv[1], "out.csv")))
"""


def run(argv, cwd, db):
    env = dict(os.environ, CRM_DB=db, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=cwd)
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout + p.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "crm.db")
        shutil.copyfile(os.path.join(ORIG, "crm.db"), self.db)
        self.old = os.path.join(self.tmp, "old")
        for pkg in ("app", "api", "exports"):
            os.makedirs(os.path.join(self.old, pkg))
            for name in os.listdir(os.path.join(ORIG, pkg)):
                shutil.copyfile(os.path.join(ORIG, pkg, name), os.path.join(self.old, pkg, name))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def migrate(self, *args):
        code, out = run([sys.executable, "migrate.py", *args], ROOT, self.db)
        self.assertEqual(code, 0, out)

    def query(self, sql):
        conn = sqlite3.connect(self.db)
        try:
            return [tuple(r) for r in conn.execute(sql)]
        finally:
            conn.close()

    def columns(self, table):
        return [r[1] for r in self.query(f"PRAGMA table_info({table})")]


class Kept(Base):
    def test_no_note_is_lost(self):
        notes = self.query("SELECT id, notes FROM contacts WHERE notes != ''")
        self.migrate("up")
        still_there = "notes" in self.columns("contacts")
        now_old = dict(self.query("SELECT id, notes FROM contacts")) if still_there else {}
        new = set(self.query("SELECT contact_id, body FROM contact_notes"))
        lost = [(cid, body) for cid, body in notes if now_old.get(cid) != body and (cid, body) not in new]
        self.assertEqual(lost, [], f"{len(lost)} notes are gone after the migration, e.g. {lost[:3]}")


class Window(Base):
    def test_old_code_runs_on_the_migrated_data(self):
        self.migrate("up")
        code, out = run([sys.executable, "-c", OLD_CODE, self.tmp], self.old, self.db)
        self.assertEqual(code, 0, "the v1 API or the export from before the release fails on the migrated "
                                  "data, and it serves requests until the services restart: " + out[-600:])


class Rollback(Base):
    def test_down_gives_back_every_contact(self):
        before = self.query("SELECT id, name, email, notes FROM contacts ORDER BY id")
        self.migrate("up")
        self.migrate("down", "2")
        self.assertIn("notes", self.columns("contacts"))
        self.assertEqual(self.query("SELECT id, name, email, notes FROM contacts ORDER BY id"), before,
                         "contacts differ after up then down")


if __name__ == "__main__":
    unittest.main()
