"""cleanup.py - the candidates it lists, and the done check that refuses a cleanup that broke something.

Each test plants the thing a rule exists to catch, so disabling that rule turns it red.
Run them all with `python -m unittest discover tests`.
"""
import json, os, re, shutil, tempfile, unittest

from _helpers import ROOT, run

TESTS = "python -m unittest discover -s tests -t ."
FILES = {
    "main.py": ("import sys\nfrom importlib import import_module\nfrom app import money\n\n\n"
                "def main(argv):\n    fmt = argv[0] if argv else 'csv'\n"
                "    print(import_module(f'app.fmt_{fmt}').render(money.cents(5)))\n\n\n"
                "if __name__ == '__main__':\n    main(sys.argv[1:])\n"),
    "config.json": '{"step": "step_v2"}\n',
    "app/__init__.py": "",
    "app/money.py": ("import os\n\n\ndef cents(n):\n    sign = '-' if n < 0 else ''\n    n = abs(n)\n"
                     "    return f'{sign}{n // 100}.{n % 100:02d}'\n\n\n"
                     "def legacy_total(rows):\n    return sum(rows)\n"),
    "app/report.py": ("from app.money import cents\n\n\n"
                      "# Updated: fixed the rounding bug (v2 rewrite)\n"
                      "def total(month):\n    if month == '2026-01':\n        return 42\n    return 0\n\n\n"
                      "def _fmt(v):\n    sign = '-' if v < 0 else ''\n    v = abs(v)\n"
                      "    return f'{sign}{v // 100}.{v % 100:02d}'\n\n\n"
                      "def show(v):\n    print('DEBUG show', v)\n    return _fmt(v) + cents(v)\n"),
    "app/importer.py": ("def load(rows):\n    out = []\n    for r in rows:\n        try:\n            out.append(int(r))\n"
                        "        except Exception:\n            pass\n    return out\n\n\n"
                        "# def load_old(rows):\n#     out = [int(r) for r in rows]\n#     return out\n"),
    "app/fmt_csv.py": "def render(s):\n    return s\n",
    "app/fmt_ofx.py": "def render(s):\n    # TODO: implement real OFX output\n    return '<OFX/>'\n",
    "app/step_v2.py": "def migrate(rows):\n    return rows\n",
    "app/report_old.py": "def total(month):\n    return 0\n",
    "SUMMARY.md": "# Summary of changes\n",
    "test_fix.py": "from app import report\nprint(report.total('2026-01'))\n",
    "tests/__init__.py": "",
    "tests/test_money.py": ("import unittest\nfrom app import money, report, importer\n\n\n"
                            "class T(unittest.TestCase):\n"
                            "    def test_cents(self):\n        self.assertEqual(money.cents(-105), '-1.05')\n"
                            "    def test_load(self):\n        self.assertEqual(importer.load(['1']), [1])\n"
                            "    def test_show(self):\n        self.assertTrue(report.show(5))\n"),
}


def write(root, rel, text):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


class Repo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = os.path.join(self._tmp.name, "repo")
        for rel, text in FILES.items():
            write(self.root, rel, text)

    def c(self, *args):
        return run("cleanup.py", self.root, *args)

    def rm(self, *rels):
        for rel in rels:
            os.remove(os.path.join(self.root, *rel.split("/")))

    def candidates(self):
        code, out, err = self.c()
        self.assertEqual(code, 0, err)
        return out


class Find(Repo):
    def test_each_planted_kind_is_listed_where_it_is(self):
        out = self.candidates()
        for kind, where in [
            ("leftover-version", "app/report_old.py"), ("leftover-version", "app/step_v2.py"),
            ("litter", "SUMMARY.md"), ("litter", "test_fix.py"),
            ("dead-function", "app/money.py:10"), ("unused-import", "app/money.py:1"),
            ("duplicate-function", "app/report.py:11"), ("duplicate-function", "app/money.py:4"),
            ("debug-leftover", "app/report.py:18"), ("swallowed-error", "app/importer.py:6"),
            ("commented-out-code", "app/importer.py:11"), ("stub", "app/fmt_ofx.py:2"),
            ("hard-coded-answer", "app/report.py:6"), ("change-log-comment", "app/report.py:4"),
        ]:
            section = re.search(r"## %s \(\d+\)\n((?:- .*\n?)*)" % kind, out)
            self.assertTrue(section, f"no {kind} section:\n{out}")
            self.assertIn(where, section.group(1), f"{kind} misses {where}:\n{out}")

    def test_used_code_is_not_called_dead(self):
        out = self.candidates()
        dead = re.search(r"## dead-function \(\d+\)\n((?:- .*\n?)*)", out).group(1)
        for live in ("cents", "show", "load", "render", "main"):
            self.assertNotRegex(dead, r"\b%s\b" % live)

    def test_candidates_are_written_to_the_state_folder(self):
        self.candidates()
        with open(os.path.join(self.root, ".cleanup", "candidates.md"), encoding="utf-8") as fh:
            self.assertIn("swallowed-error", fh.read())

    def test_paths_limit_the_scan(self):
        code, out, _ = self.c("app/importer.py")
        self.assertIn("swallowed-error", out)
        self.assertNotIn("SUMMARY.md", out)


class Baseline(Repo):
    def test_records_files_and_tests(self):
        code, out, err = self.c("--run", TESTS)
        self.assertEqual(code, 0, out + err)
        with open(os.path.join(self.root, ".cleanup", "baseline.json"), encoding="utf-8") as fh:
            base = json.load(fh)
        self.assertEqual(base["suite"]["ran"], 3)
        self.assertIn("app/report_old.py", base["files"])

    def test_a_command_that_ran_no_tests_records_nothing(self):
        code, out, _ = self.c("--run", "python -c \"print('hi')\"")
        self.assertEqual(code, 1)
        self.assertIn("ran no tests", out)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".cleanup", "baseline.json")))

    def test_done_without_a_baseline_is_refused(self):
        code, out, _ = self.c("--done")
        self.assertEqual(code, 1)
        self.assertIn("no baseline", out)


class Done(Repo):
    def setUp(self):
        super().setUp()
        code, out, err = self.c("--run", TESTS)
        self.assertEqual(code, 0, out + err)

    def test_a_clean_cleanup_is_done_and_recorded(self):
        self.rm("app/report_old.py", "test_fix.py", "SUMMARY.md")
        code, out, _ = self.c("--done")
        self.assertEqual(code, 0, out)
        self.assertIn("CLEANUP: done", out)
        with open(os.path.join(self.root, ".cleanup", "history.json"), encoding="utf-8") as fh:
            hist = json.load(fh)
        self.assertEqual(sorted(hist[-1]["deleted"]), ["SUMMARY.md", "app/report_old.py", "test_fix.py"])
        self.assertFalse(os.path.exists(os.path.join(self.root, ".cleanup", "baseline.json")))

    def test_a_test_that_passed_and_now_fails_is_refused(self):
        write(self.root, "app/importer.py", "def load(rows):\n    return []\n")
        code, out, _ = self.c("--done")
        self.assertEqual(code, 1)
        self.assertIn("passed before and fail now", out)
        self.assertNotIn("CLEANUP: done", out)

    def test_fewer_tests_is_refused(self):
        write(self.root, "tests/test_money.py", "import unittest\n\n\nclass T(unittest.TestCase):\n"
                                               "    def test_one(self):\n        pass\n")
        code, out, _ = self.c("--done")
        self.assertEqual(code, 1)
        self.assertIn("1 tests ran, 3 before", out)

    def test_deleting_a_file_still_named_in_config_is_refused(self):
        self.rm("app/step_v2.py")
        code, out, _ = self.c("--done")
        self.assertEqual(code, 1)
        self.assertIn("step_v2", out)
        self.assertIn("config.json", out)

    def test_nothing_is_recorded_while_refused(self):
        self.rm("app/step_v2.py")
        self.c("--done")
        self.assertFalse(os.path.exists(os.path.join(self.root, ".cleanup", "history.json")))


class SinceLast(Repo):
    def test_the_next_run_shows_what_came_back_and_what_is_new(self):
        self.c("--run", TESTS)
        self.rm("app/report_old.py", "test_fix.py", "SUMMARY.md")
        self.assertEqual(self.c("--done")[0], 0)
        write(self.root, "test_fix.py", "print(1)\n")
        write(self.root, "app/money_new.py", "def cents(n):\n    return n\n")
        out = self.candidates()
        head = out.split("## ")[0]
        self.assertIn("came back: test_fix.py", head)
        self.assertIn("new: leftover-version app/money_new.py", head)
        self.assertNotIn("importer.py", head, "candidates left last time are not new")

    def test_no_record_means_no_since_section(self):
        self.assertNotIn("Since the cleanup", self.candidates())


class Skill(unittest.TestCase):
    def test_skill_is_short_manual_and_names_its_helper(self):
        with open(os.path.join(ROOT, "plugin", "skills", "cleanup", "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        head, body = text.split("---", 2)[1:]
        self.assertIn("disable-model-invocation: true", head)
        self.assertLessEqual(len(body), 3000)
        self.assertIn("scripts/cleanup.py", body)
        self.assertIn("--done", body)


if __name__ == "__main__":
    unittest.main()
