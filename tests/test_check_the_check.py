"""check-the-check's helper: each probe fires on the eval fixture built to need it, and never
writes to the repo it checks."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from _helpers import ROOT

CHECK = os.path.join(ROOT, "plugin", "skills", "check-the-check", "scripts", "check.py")
CASES = os.path.join(ROOT, "evals", "cases")


def tree(folder):
    out = {}
    for base, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for name in files:
            path = os.path.join(base, name)
            with open(path, "rb") as fh:
                out[os.path.relpath(path, folder)] = hashlib.sha256(fh.read()).hexdigest()
    return out


def write(folder, files):
    for rel, text in files.items():
        path = os.path.join(folder, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


class CheckTheCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ctc-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def fixture(self, case):
        repo = os.path.join(self.tmp, "repo")
        shutil.copytree(os.path.join(CASES, case, "fixture"), repo)
        setup = os.path.join(CASES, case, "setup.py")
        if os.path.isfile(setup):
            subprocess.run([sys.executable, setup, repo], check=True, capture_output=True)
        return repo

    def check(self, repo, *args):
        before = tree(repo)
        status = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True).stdout \
            if os.path.isdir(os.path.join(repo, ".git")) else None
        p = subprocess.run([sys.executable, CHECK, repo, *args], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(tree(repo), before, "the helper wrote into the repo it checked")
        if status is not None:
            self.assertEqual(subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True,
                                            text=True).stdout, status)
        return p.returncode, p.stdout + p.stderr

    def test_survivors_in_a_big_suite(self):
        code, out = self.check(self.fixture("check-the-check-survivors-in-a-big-suite"),
                               "--check", "python -m unittest test_billing", "--max-mutants", "200")
        self.assertEqual(code, 1, out)
        self.assertIn("SURVIVED   billing.py:45  `return [base + 1", out)
        self.assertIn("`VOLUME_TIERS = [(50, 15), (21, 10), (10, 5)]", out)
        self.assertIn("LINES      billing.py: 29/29 statements ran", out)

    def test_tests_that_never_run(self):
        code, out = self.check(self.fixture("check-the-check-tests-that-never-run"),
                               "--check", "python -m unittest test_points")
        self.assertEqual(code, 1, out)
        self.assertIn("NEVER RAN  test_points.py:20 PointsEarnedTest.test_gold_earns_double", out)
        self.assertIn("PRODUCT    points.py ", out)  # the fixtures module is test support
        self.assertIn("(that line never runs)", out)

    def test_a_test_file_the_command_never_loads(self):
        code, out = self.check(self.fixture("check-the-check-ci-skips-a-test-file"),
                               "--check", "python -m unittest discover -s tests -t .")
        self.assertEqual(code, 1, out)
        self.assertIn("NEVER LOADED tests/refund_rules_test.py  (5 test functions)", out)
        self.assertNotIn("SURVIVED", out)  # error messages are not mutated

    def test_a_new_test_that_passes_before_the_change(self):
        code, out = self.check(self.fixture("check-the-check-regression-test-misses-fix"),
                               "--check", "python -m unittest test_billing", "--base", "main")
        self.assertEqual(code, 1, out)
        self.assertIn("BASE       main: put back billing.py; check passes there", out)
        self.assertIn("NEW TEST   test_billing.py:16 LateFeeTest.test_due_date_is_not_late  PASSES there", out)

    def test_a_new_test_that_fails_before_the_change_proves_it(self):
        repo = self.fixture("check-the-check-regression-test-misses-fix")
        with open(os.path.join(repo, "test_billing.py"), encoding="utf-8") as fh:
            text = fh.read()
        write(repo, {"test_billing.py": text.replace("late_fee(DUE, DUE, 200.0), 0.0)", "invoice_total(200.0, DUE, DUE), 200.0)")})
        _, out = self.check(repo, "--check", "python -m unittest test_billing", "--base", "main")
        self.assertIn("test_due_date_is_not_late  fails there, passes now", out)

    def test_strong_check(self):
        write(self.tmp, {"calc.py": "def add(a, b):\n    return a + b\n",
                         "test_calc.py": "import unittest\nfrom calc import add\n\n\nclass T(unittest.TestCase):\n"
                                         "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n"})
        code, out = self.check(self.tmp, "--check", "python -m unittest test_calc")
        self.assertEqual(code, 0, out)
        self.assertIn("VERDICT    strong", out)

    def test_hollow_check(self):
        write(self.tmp, {"calc.py": "def add(a, b):\n    return a + b\n",
                         "test_calc.py": "import unittest\nimport calc\n\n\nclass T(unittest.TestCase):\n"
                                         "    def test_add(self):\n        self.assertEqual(2 + 3, 5)\n"})
        code, out = self.check(self.tmp, "--check", "python -m unittest test_calc")
        self.assertEqual(code, 1, out)
        self.assertIn("HOLLOW     calc.py", out)

    def test_red_check_is_reported_not_judged(self):
        write(self.tmp, {"calc.py": "def add(a, b):\n    return a - b\n",
                         "test_calc.py": "import unittest\nfrom calc import add\n\n\nclass T(unittest.TestCase):\n"
                                         "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n"})
        code, out = self.check(self.tmp, "--check", "python -m unittest test_calc")
        self.assertEqual(code, 2, out)
        self.assertIn("FAILING    test_calc.py:6 T.test_add", out)

    def test_a_check_that_cannot_start_is_blocked(self):
        code, out = self.check(self.tmp, "--check", "no-such-tool-ctc --run")
        self.assertEqual(code, 3, out)

    def test_json(self):
        repo = self.fixture("check-the-check-tests-that-never-run")
        p = subprocess.run([sys.executable, CHECK, repo, "--check", "python -m unittest test_points", "--json"],
                           capture_output=True, text=True, encoding="utf-8")
        r = json.loads(p.stdout)
        self.assertEqual(r["verdict"], "weak")
        self.assertEqual({x["kind"] for x in r["findings"]}, {"never-ran", "survived"})


if __name__ == "__main__":
    unittest.main()
