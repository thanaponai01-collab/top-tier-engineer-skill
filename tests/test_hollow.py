"""1.15.0: a check that passes without running the product is HOLLOW, module-style test commands map
to their files, and `challenge --auto` finds its file in `path:` and surveys without a fail-signal.

Run with: python -m unittest discover tests
"""
import json, tempfile, unittest
from pathlib import Path

from _helpers import run

REFUND = "def apply_refund(credit, amount):\n    return credit + amount\n"
LOADER = ("import json, os, unittest\nfrom refund import apply_refund\n\n"
          "def load_cases():\n    p = 'cases/refunds.json'\n"
          "    return json.load(open(p)) if os.path.exists(p) else []\n\n"
          "class T(unittest.TestCase):\n    def test_cases(self):\n        for c in load_cases():\n"
          "            self.assertEqual(apply_refund(c['credit'], c['amount']), c['want'])\n")


def write(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def project(root, test=LOADER, product=REFUND, command="python -m unittest test_refund -q", path="refund.py"):
    write(root, "refund.py", product)
    write(root, "test_refund.py", test)
    write(root, "VERIFY.md", f"## Refunds\n- path: {path}\n- test: `{command}`\n- fail-signal: AssertionError\n")


class Hollow(unittest.TestCase):
    def test_check_that_loads_no_cases_is_hollow_and_red(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 1, out)
            self.assertIn("HOLLOW", out)
            self.assertIn("| 1 hollow", out)
            code, out, _ = run("verify.py", "run", root, "--json")
            self.assertEqual(json.loads(out)["summary"]["hollow"], ["Refunds"])

    def test_check_that_calls_the_product_is_not_hollow(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            write(root, "cases/refunds.json", '[{"credit": 100, "amount": 50, "want": 150}]')
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 0, out)
            self.assertNotIn("HOLLOW", out)

    def test_import_alone_does_not_count_as_reaching_the_product(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, test="from refund import apply_refund\nassert 100 + 50 == 150, 'AssertionError'\n",
                    command="python test_refund.py")
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 1, out)
            self.assertIn("HOLLOW", out)

    def test_hollow_pass_is_never_cached(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            run("verify.py", "run", root)
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 1, out)
            self.assertIn("HOLLOW", out)
            self.assertNotIn("CACHED", out)

    def test_module_without_functions_is_not_judged(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, product="RATE = 5\n", test="from refund import RATE\nassert RATE == 5\n",
                    command="python test_refund.py")
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 0, out)
            self.assertNotIn("HOLLOW", out)

    def test_check_with_no_python_process_is_not_judged(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, command="git --version")
            code, out, _ = run("verify.py", "run", root)
            self.assertNotIn("HOLLOW", out)

    def test_run_check_is_not_judged(self):
        """A `run:` check drives an app the measurement does not see."""
        with tempfile.TemporaryDirectory() as root:
            project(root)
            write(root, "VERIFY.md", "## Refunds\n- path: refund.py\n- run: `python -c \"pass\"`\n")
            code, out, _ = run("verify.py", "run", root)
            self.assertNotIn("HOLLOW", out)

    def test_feature_under_a_run_recipe_is_not_judged(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            write(root, "VERIFY.md", Path(root, "VERIFY.md").read_text()
                  + "\n## Run\n- setup: `python -c \"pass\"`\n")
            code, out, _ = run("verify.py", "run", root)
            self.assertNotIn("HOLLOW", out)

    def test_without_path_imported_but_never_called_is_hollow(self):
        """The eval fixture: no `path:`, the test imports refund.py and loops over no cases."""
        with tempfile.TemporaryDirectory() as root:
            project(root)
            write(root, "VERIFY.md", "## Refunds\n- test: `python -m unittest test_refund.py`\n")
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 1, out)
            self.assertIn("HOLLOW", out)
            self.assertIn("refund.py (imported, never called)", out)

    def test_without_path_one_product_call_clears_it(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            write(root, "cases/refunds.json", '[{"credit": 100, "amount": 50, "want": 150}]')
            write(root, "unused.py", "def spare():\n    return 0\n")
            write(root, "test_refund.py", "import unused\n" + LOADER)
            write(root, "VERIFY.md", "## Refunds\n- test: `python -m unittest test_refund.py`\n")
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 0, out)
            self.assertNotIn("HOLLOW", out)

    def test_without_path_a_check_that_imports_nothing_is_not_judged(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, command="python -c \"pass\"")
            write(root, "VERIFY.md", "## Refunds\n- test: `python -c \"pass\"`\n")
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 0, out)
            self.assertNotIn("HOLLOW", out)


class ModuleNames(unittest.TestCase):
    def test_unittest_module_name_maps_its_file(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            code, out, _ = run("verify.py", "tests", root)
            self.assertIn("1 mapped to a feature | 0 unmapped", out)
            self.assertNotIn("Orphan tests", run("verify.py", "run", root)[1])

    def test_dotted_package_module_maps_its_file(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, command="python -m unittest tests.test_refund.T.test_cases")
            write(root, "tests/__init__.py", "")
            write(root, "tests/test_refund.py", Path(root, "test_refund.py").read_text())
            Path(root, "test_refund.py").unlink()
            out = run("verify.py", "tests", root)[1]
            self.assertIn("tests/test_refund.py::T.test_cases", out.split("Unmapped")[0])

    def test_a_different_module_does_not_map(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, command="python -m unittest test_ref")
            out = run("verify.py", "tests", root)[1]
            self.assertIn("0 mapped to a feature | 1 unmapped", out)


class AutoDefaults(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        write(self.root, "app.py", "def grade(score):\n    if score >= 50:\n        return 'pass'\n    return 'fail'\n")
        write(self.root, "test_grade.py", "from app import grade\nassert grade(50) == 'pass', 'expected pass'\n"
                                          "assert grade(49) == 'fail', 'expected fail'\n")

    def tearDown(self):
        self.tmp.cleanup()

    def recipe(self, extra):
        write(self.root, "VERIFY.md", "## Grade\n- test: `python test_grade.py`\n" + extra)

    def test_auto_without_file_mutates_the_path_files(self):
        self.recipe("- path: app.py\n- fail-signal: expected\n")
        code, out, err = run("verify.py", "challenge", self.root, "--feature", "Grade", "--auto", "--json")
        self.assertEqual(code, 0, out + err)
        summary = json.loads(out)
        self.assertEqual(summary["files"], ["app.py"])
        self.assertGreaterEqual(summary["caught"], 2)

    def test_auto_without_file_or_path_says_what_is_missing(self):
        self.recipe("- fail-signal: expected\n")
        code, out, _ = run("verify.py", "challenge", self.root, "--feature", "Grade", "--auto")
        self.assertEqual(code, 2, out)
        self.assertIn("`path:`", out)

    def test_auto_surveys_without_a_fail_signal(self):
        self.recipe("- path: app.py\n")
        code, out, err = run("verify.py", "challenge", self.root, "--feature", "Grade", "--auto")
        self.assertEqual(code, 0, out + err)
        self.assertIn("no fail-signal declared", out)
        self.assertIn("score 100%", out)
        self.assertFalse(Path(self.root, ".verify-state.json").exists()
                         and json.loads(Path(self.root, ".verify-state.json").read_text()).get("failures"))


if __name__ == "__main__":
    unittest.main()
