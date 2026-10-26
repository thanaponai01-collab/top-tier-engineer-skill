#!/usr/bin/env python3
"""
release.py - the rehearsal and the gate behind safe-release.

Each test plants the thing a guard exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import hashlib, os, sqlite3, subprocess, tempfile, unittest

from _helpers import run

APP = ("import os, sqlite3\n"
       "DB = os.environ.get('APP_DB', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'app.db'))\n\n\n"
       "def add(name):\n    c = sqlite3.connect(DB)\n    c.execute('INSERT INTO items (name) VALUES (?)', (name,))\n"
       "    c.commit()\n    c.close()\n\n\n"
       "def names():\n    c = sqlite3.connect(DB)\n    r = [x[0] for x in c.execute('SELECT name FROM items ORDER BY id')]\n"
       "    c.close()\n    return r\n")
WRITE_PROBE = "import app\napp.add('probe')\nprint(app.names())\n"
READ_PROBE = "import app\nprint(app.names())\n"
# A step guarded by the file's user_version, the way a migration runner records what it applied.
DB_SCRIPT = ("import os, sqlite3\nc = sqlite3.connect(os.environ.get('APP_DB', 'data/app.db'))\n"
             "if c.execute('PRAGMA user_version').fetchone()[0] == {at}:\n    {body}\n"
             "    c.execute('PRAGMA user_version = {to}')\nc.commit()\nc.close()\n")
UNGUARDED = "import os, sqlite3\nc = sqlite3.connect(os.environ.get('APP_DB', 'data/app.db'))\n{body}\nc.commit()\nc.close()\n"
# forward steps
ADD_COLUMN = "c.execute(\"ALTER TABLE items ADD COLUMN size TEXT NOT NULL DEFAULT 'm'\")"
DROP_ADDED = "c.execute('ALTER TABLE items DROP COLUMN size')"
RENAME = "c.execute('ALTER TABLE items RENAME COLUMN name TO title')"
RENAME_BACK = "c.execute('ALTER TABLE items RENAME COLUMN title TO name')"
REBUILD_NO_UNIQUE = ("c.executescript('CREATE TABLE n (id INTEGER PRIMARY KEY, name TEXT NOT NULL); "
                     "INSERT INTO n SELECT id, name FROM items; DROP TABLE items; ALTER TABLE n RENAME TO items;')")
REBUILD_UNIQUE = ("c.executescript('CREATE TABLE n (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE); "
                  "INSERT INTO n SELECT id, name FROM items; DROP TABLE items; ALTER TABLE n RENAME TO items;')")
ADD_ROW = "c.execute(\"INSERT INTO items (name) VALUES ('seeded')\")"
DROP_ROW = "c.execute(\"DELETE FROM items WHERE name = 'seeded'\")"
CLEAR_NAMES = "c.execute(\"UPDATE items SET name = name || '-' || id\")"
NOTHING = "pass"
FWD, BACK = "python fwd.py", "python back.py"
PROBE = "python .release/probes/write.py"
PLAN_OK = ("CALL: ship, nothing risky\nROLLBACK: python back.py, then deploy the previous version\n"
           "NO-RETURN: none\nWATCH: error rate on item writes\n")


def make(tmp, forward=ADD_COLUMN, back=DROP_ADDED, probe=WRITE_PROBE):
    files = {"app.py": APP, ".release/probes/write.py": probe,
             "fwd.py": DB_SCRIPT.format(body=forward, at=0, to=1), "back.py": DB_SCRIPT.format(body=back, at=1, to=0)}
    for rel, text in files.items():
        p = os.path.join(tmp, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    os.makedirs(os.path.join(tmp, "data"), exist_ok=True)
    c = sqlite3.connect(os.path.join(tmp, "data", "app.db"))
    c.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)")
    c.executemany("INSERT INTO items (name) VALUES (?)", [("a",), ("b",), ("c",)])
    c.commit()
    c.close()


def write(tmp, rel, text):
    p = os.path.join(tmp, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def live_sha(tmp):
    with open(os.path.join(tmp, "data", "app.db"), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class Rehearsal(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp = self.t.name

    def tearDown(self):
        self.t.cleanup()

    def start(self, **kw):
        """The repo as it runs today, R called before any change, then the change written."""
        forward, back = kw.pop("forward", ADD_COLUMN), kw.pop("back", DROP_ADDED)
        unguarded = kw.pop("unguarded", False)
        make(self.tmp, NOTHING, NOTHING, **kw)
        os.remove(os.path.join(self.tmp, "fwd.py"))
        os.remove(os.path.join(self.tmp, "back.py"))
        code, out, err = run("release.py", self.tmp)
        self.assertEqual(code, 0, out + err)
        write(self.tmp, "fwd.py", (UNGUARDED if unguarded else DB_SCRIPT).format(body=forward, at=0, to=1))
        write(self.tmp, "back.py", DB_SCRIPT.format(body=back, at=1, to=0))

    def rehearse(self, *extra, probe=PROBE, back=BACK):
        args = [self.tmp, "--rehearse", "--forward", FWD, "--probe", probe, *extra]
        if back:
            args += ["--back", back]
        code, out, err = run("release.py", *args)
        self.assertEqual(code, 0, out + err)
        return out

    def gate(self):
        code, out, err = run("release.py", self.tmp, "--gate")
        return code, out + err

    def plan(self, text=PLAN_OK, carries=("fwd.py", "back.py")):
        write(self.tmp, ".release/plan.md", text + "".join(f"- CARRIES {c}: changes the data\n" for c in carries))

    def stage(self, out, n):
        line = next(ln for ln in out.splitlines() if ln.startswith(f"STAGE {n}"))
        return line.endswith("holds")

    # the path that holds
    def test_an_additive_change_with_a_lossless_way_back_is_done(self):
        self.start()
        self.rehearse()
        self.plan()
        code, out = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("RELEASE-GATE: done(ship, lossless way back)", out)
        self.assertIn("deploy window and a code-only revert are safe", out)

    # stage 1
    def test_nothing_rehearsed_is_open(self):
        make(self.tmp)
        code, out = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("nothing rehearsed", out)

    def test_a_forward_step_that_changes_no_data_is_refused(self):
        self.start(forward=NOTHING, back=NOTHING)
        out = self.gate()[1] if self.rehearse() else ""
        self.assertIn("forward changed nothing in the data", out)

    def test_a_forward_step_that_is_not_safe_to_run_twice_is_refused(self):
        self.start(forward=ADD_ROW, back=DROP_ROW, unguarded=True)
        self.rehearse()
        self.assertIn("forward is not safe to run twice", self.gate()[1])

    def test_a_read_only_rehearsal_is_refused(self):
        self.start(probe=READ_PROBE)
        self.rehearse()
        self.assertIn("no probe writes to the data", self.gate()[1])

    def test_a_probe_that_fails_on_todays_code_is_refused(self):
        self.start(probe="import app\napp.add(None)\n")
        self.rehearse()
        self.assertIn("fails on today's code and today's data", self.gate()[1])

    def test_a_dropped_constraint_must_be_kept_or_named(self):
        self.start(forward=REBUILD_NO_UNIQUE, back=REBUILD_UNIQUE)
        out = self.rehearse()
        self.assertIn("constraint dropped by forward: data/app.db: items unique on name", out)
        self.plan()
        code, out = self.gate()
        self.assertIn("forward drops a constraint: data/app.db: items unique on name", out)
        write(self.tmp, ".release/plan.md", PLAN_OK + "- CARRIES fwd.py: x\n- CARRIES back.py: y\n"
              "- DROPS data/app.db: items unique on name: names repeat across shops now\n")
        self.assertTrue(self.stage(self.gate()[1], 1))

    def test_a_forward_step_that_fails_is_open(self):
        self.start(forward="raise SystemExit(3)")
        self.rehearse()
        self.assertIn("fails on a copy of the live data (exit 3)", self.gate()[1])

    def test_the_changed_code_failing_on_the_migrated_data_is_open(self):
        self.start(forward=RENAME, back=RENAME_BACK)
        self.rehearse()
        self.assertIn("fails on the changed code with the migrated data", self.gate()[1])

    def test_changing_the_code_after_the_rehearsal_makes_it_stale(self):
        self.start()
        self.rehearse()
        write(self.tmp, "app.py", APP + "\n# changed\n")
        self.assertIn("the code changed since the rehearsal", self.gate()[1])

    # stage 2
    def test_todays_code_failing_on_the_migrated_data_opens_the_window(self):
        self.start(forward=RENAME, back=RENAME_BACK)
        write(self.tmp, "app.py", APP.replace("name", "title").replace("def title", "def name"))
        self.rehearse()
        self.plan(carries=("app.py", "fwd.py", "back.py"))
        code, out = self.gate()
        self.assertIn("today's code fails on the migrated data", out)
        self.assertFalse(self.stage(out, 2))
        self.plan(PLAN_OK + "WINDOW: both services are stopped before the migration and started after\n",
                  carries=("app.py", "fwd.py", "back.py"))
        self.assertTrue(self.stage(self.gate()[1], 2))

    def test_a_new_required_column_no_probe_caught_is_named(self):
        self.start(forward="c.execute(\"ALTER TABLE items ADD COLUMN size TEXT NOT NULL DEFAULT 'm'\")\n"
                           "    c.executescript('CREATE TABLE n (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, "
                           "size TEXT NOT NULL); INSERT INTO n SELECT id, name, size FROM items; DROP TABLE items; "
                           "ALTER TABLE n RENAME TO items;')",
                   probe="import os, sqlite3\nc = sqlite3.connect(os.environ.get('APP_DB', 'data/app.db'))\n"
                         "c.execute('UPDATE items SET id = id')\nc.execute(\"DELETE FROM items WHERE name = 'c'\")\n"
                         "c.commit()\nc.close()\n")
        self.rehearse()
        self.assertIn("new NOT NULL column with no default: data/app.db: items.size", self.gate()[1])

    def test_a_way_back_that_fails_is_open(self):
        self.start(back="raise SystemExit(4)")
        self.rehearse()
        self.assertIn("fails after forward on a copy (exit 4)", self.gate()[1])

    def test_todays_code_failing_after_the_way_back_is_open(self):
        self.start(forward=RENAME, back=NOTHING)
        write(self.tmp, "app.py", APP.replace("name", "title").replace("def title", "def name"))
        self.rehearse()
        self.assertIn("after the way back, today's code fails", self.gate()[1])

    def test_no_way_back_is_open(self):
        self.start()
        self.rehearse(back=None)
        self.assertIn("no way back rehearsed", self.gate()[1])

    def test_a_lossy_way_back_must_name_the_loss(self):
        self.start(forward=CLEAR_NAMES, back=NOTHING)
        self.rehearse()
        self.plan()
        code, out = self.gate()
        self.assertIn("the way back does not give the data back", out)
        self.assertIn("NO-RETURN says none", out)
        self.assertIn("name the loss: `- LOSES data/app.db: items has 3 changed row(s): <the step", out)
        self.plan(PLAN_OK.replace("NO-RETURN: none", "NO-RETURN: the forward step; every name is rewritten")
                  + "- LOSES data/app.db: items has 3 changed row(s): forward rewrites every name for good\n")
        code, out = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("lossy way back", out)

    def test_todays_code_is_taken_from_git_head(self):
        make(self.tmp, forward=RENAME, back=RENAME_BACK)
        for args in (["init", "-q"], ["add", "app.py"], ["-c", "user.name=t", "-c", "user.email=t@t",
                                                         "commit", "-q", "-m", "today"]):
            subprocess.run(["git", *args], cwd=self.tmp, check=True, capture_output=True)
        write(self.tmp, "app.py", APP.replace("name", "title").replace("def title", "def name"))
        self.rehearse()
        out = self.gate()[1]
        self.assertIn("today's code fails on the migrated data", out)

    # stage 3
    def test_the_plan_slots_are_appended_and_must_be_filled(self):
        self.start()
        self.rehearse()
        code, out = self.gate()
        for key in ("CALL", "ROLLBACK", "NO-RETURN", "WATCH"):
            self.assertIn(f".release/plan.md: {key} is not filled", out)
        self.assertIn("the release carries fwd.py", out)
        with open(os.path.join(self.tmp, ".release", "plan.md"), encoding="utf-8") as fh:
            self.assertIn("- CARRIES fwd.py: [[fill", fh.read())

    def test_tests_and_docs_are_not_carried(self):
        self.start()
        write(self.tmp, "tests/test_items.py", "x = 1\n")
        write(self.tmp, "NOTES.md", "x\n")
        self.rehearse()
        out = self.gate()[1]
        self.assertNotIn("carries tests/test_items.py", out)
        self.assertNotIn("carries NOTES.md", out)

    def test_the_call_is_ship_stage_or_hold(self):
        self.start()
        self.rehearse()
        self.plan(PLAN_OK.replace("CALL: ship", "CALL: probably fine"))
        self.assertIn("CALL starts with ship, stage or hold", self.gate()[1])

    def test_the_rollback_names_the_rehearsed_way_back(self):
        self.start()
        self.rehearse()
        self.plan(PLAN_OK.replace("python back.py, then", "just"))
        self.assertIn("ROLLBACK does not include the rehearsed way back", self.gate()[1])

    def test_a_carries_line_for_an_unchanged_file_is_refused(self):
        self.start()
        self.rehearse()
        self.plan(carries=("fwd.py", "back.py", "app.py"))
        self.assertIn("CARRIES app.py, which is not changed", self.gate()[1])

    def test_a_hold_with_rehearsed_blockers_is_a_finished_answer(self):
        self.start(forward=RENAME, back=RENAME_BACK)
        self.rehearse()
        self.plan(PLAN_OK.replace("CALL: ship, nothing risky", "CALL: hold, the rename breaks every writer"))
        code, out = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("RELEASE-GATE: done(hold, ", out)
        self.assertIn("Why it holds", out)

    def test_a_hold_on_a_stale_rehearsal_is_not_finished(self):
        self.start(forward=RENAME, back=RENAME_BACK)
        self.rehearse()
        self.plan(PLAN_OK.replace("CALL: ship, nothing risky", "CALL: hold, the rename breaks every writer"))
        write(self.tmp, "fwd.py", DB_SCRIPT.format(body=ADD_COLUMN, at=0, to=1))
        code, out = self.gate()
        self.assertEqual(code, 1, out)
        self.assertIn("the code changed since the rehearsal", out)

    def test_a_rehearsal_that_reaches_the_live_data_is_caught(self):
        self.start(forward="c.close()\n    c = sqlite3.connect(" + repr(os.path.join(self.tmp, "data", "app.db"))
                   + ")\n    " + ADD_COLUMN)
        self.rehearse()
        self.assertIn("the live data changed while the rehearsal ran", self.gate()[1])

    def test_the_live_data_changed_after_the_first_call_is_caught(self):
        self.start()
        self.rehearse()
        self.plan()
        c = sqlite3.connect(os.path.join(self.tmp, "data", "app.db"))
        c.execute("INSERT INTO items (name) VALUES ('live write')")
        c.commit()
        c.close()
        self.assertIn("the live data data/app.db is not as it was", self.gate()[1])

    def test_a_variable_aimed_at_the_live_data_does_not_reach_it(self):
        self.start()
        before = live_sha(self.tmp)
        old = os.environ.get("APP_DB")
        os.environ["APP_DB"] = os.path.join(self.tmp, "data", "app.db")
        try:
            self.rehearse()
        finally:
            if old is None:
                del os.environ["APP_DB"]
            else:
                os.environ["APP_DB"] = old
        self.assertEqual(live_sha(self.tmp), before)


if __name__ == "__main__":
    unittest.main()
