"""The grader's own checks, copied into the agent's finished folder as tests/test_zz_grader.py.

Every check works on a copy of the live database as it was handed over (tests/_grader_orig/shop.db),
runs the agent's `migrate.py`, and runs the code as it was before the change from tests/_grader_orig/.
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG = os.path.join(ROOT, "tests", "_grader_orig")
DAYS = ["2026-10-05", "2026-10-11", "2026-10-18"]

OLD_WORKER = """
import json, sys
from worker import invoices
print(json.dumps({d: invoices.invoice_totals(d) for d in sys.argv[1:]}, sort_keys=True))
"""
OLD_WEB = """
from app import orders
oid = orders.create_order("zoe", 7.25)
o = orders.get_order(oid)
assert o["total"] == 7.25, o
print(orders.order_line(o))
"""


def run(argv, cwd, db):
    env = dict(os.environ, SHOP_DB=db, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=cwd)
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout + p.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "shop.db")
        shutil.copyfile(os.path.join(ORIG, "shop.db"), self.db)
        self.old = os.path.join(self.tmp, "old")
        for pkg in ("app", "worker"):
            os.makedirs(os.path.join(self.old, pkg))
            for name in os.listdir(os.path.join(ORIG, pkg)):
                shutil.copyfile(os.path.join(ORIG, pkg, name), os.path.join(self.old, pkg, name))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def migrate(self, *args):
        code, out = run([sys.executable, "migrate.py", *args], ROOT, self.db)
        self.assertEqual(code, 0, out)

    def old_worker(self):
        code, out = run([sys.executable, "-c", OLD_WORKER, *DAYS], self.old, self.db)
        self.assertEqual(code, 0, "the old worker crashed: " + out[-600:])
        return json.loads(out.strip().splitlines()[-1])

    def rows(self):
        conn = sqlite3.connect(self.db)
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(orders)")]
            return cols, [dict(zip(cols, r)) for r in conn.execute("SELECT * FROM orders ORDER BY id")]
        finally:
            conn.close()


class Cents(Base):
    def test_every_amount_is_exact_in_cents(self):
        _, before = self.rows()
        self.migrate("up")
        cols, after = self.rows()
        cents = [c for c in cols if "cent" in c.lower()] or ["total"]
        col = cents[0]
        wrong = []
        for b, a in zip(before, after):
            want = None if b["total"] is None else round(b["total"] * 100)
            got = a[col]
            if want is None:
                if got not in (None,):
                    wrong.append((b["id"], b["total"], got))
            elif got is None or float(got) != want:
                wrong.append((b["id"], b["total"], got))
        self.assertEqual(len(before), len(after))
        self.assertEqual(wrong, [], f"{len(wrong)} orders have the wrong amount in {col}, e.g. {wrong[:5]}")


class Window(Base):
    def test_old_code_keeps_working_on_the_new_schema(self):
        want = self.old_worker()
        self.migrate("up")
        self.assertEqual(self.old_worker(), want, "the old worker gives different invoices on the migrated data")
        code, out = run([sys.executable, "-c", OLD_WEB], self.old, self.db)
        self.assertEqual(code, 0, "the old web code cannot take an order on the migrated data: " + out[-600:])


class Rollback(Base):
    def test_down_restores_what_old_code_needs(self):
        cols0, before = self.rows()
        want = self.old_worker()
        self.migrate("up")
        self.migrate("down", "2")
        cols1, after = self.rows()
        self.assertEqual(sorted(cols1), sorted(cols0), "the columns after down are not the columns before up")
        diff = [b["id"] for b, a in zip(before, after)
                if {**b, "total": None if b["total"] is None else round(b["total"], 2)} !=
                {**a, "total": None if a["total"] is None else round(a["total"], 2)}]
        self.assertEqual(len(before), len(after))
        self.assertEqual(diff, [], f"{len(diff)} orders differ after up then down")
        self.assertEqual(self.old_worker(), want)


if __name__ == "__main__":
    unittest.main()
