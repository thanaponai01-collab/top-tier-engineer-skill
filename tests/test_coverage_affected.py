"""1.11.0: `run --record-coverage` maps each check to the repo files it executes (when coverage.py is
importable), and `--affected` selects by that map as well as by file names. A selection can miss a
dependency, so `--affected` never makes `--strict` green.

Run with: python -m unittest discover tests
"""
import importlib.util, json, os, subprocess, tempfile, time, unittest
from pathlib import Path

from _helpers import run

HAS_COVERAGE = importlib.util.find_spec("coverage") is not None


def write(root, rel, text, age=10):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    t = time.time() - age
    os.utime(p, (t, t))


def git(root, *args):
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True)


def project(root):
    """Calc's check imports helpers/mathx.py; no command names that file. Both checks are seen red
    with their signal, frozen, and green under --strict before a test edits anything."""
    write(root, "helpers/__init__.py", "")
    write(root, "helpers/mathx.py", "def double(x):\n    return x * 3\n")
    write(root, "other.py", "def two():\n    return 3\n")
    write(root, "check_calc.py", "from helpers.mathx import double\nassert double(2) == 4, 'expected 4'\n")
    write(root, "check_other.py", "from other import two\nassert two() == 2, 'expected 2'\n")
    write(root, "VERIFY.md", "## Calc\n- test: `python check_calc.py`\n- fail-signal: expected 4\n"
                             "- fail-proof: double tripled, check went red\n\n"
                             "## Other\n- test: `python check_other.py`\n- fail-signal: expected 2\n"
                             "- fail-proof: two returned 3, check went red\n")
    git(root, "init", "-q")
    assert run("verify.py", "run", root)[0] == 1  # the receipts: both red with their signal
    write(root, "helpers/mathx.py", "def double(x):\n    return x * 2\n")
    write(root, "other.py", "def two():\n    return 2\n")
    assert run("verify.py", "baseline", root)[0] == 0
    code, out, _ = run("verify.py", "run", root, "--strict")
    assert code == 0, out
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x")


def affected_names(root):
    code, out, _ = run("verify.py", "run", root, "--affected", "--json", "--no-cache")
    return code, sorted(r["feature"] for r in json.loads(out)["results"])


class AffectedNeverStrictGreen(unittest.TestCase):
    def test_strict_affected_run_stays_red_even_when_every_selected_check_passes(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            write(root, "other.py", "def two():\n    return 1 + 1\n", age=20)
            self.assertEqual(run("verify.py", "run", root, "--strict")[0], 0)  # the whole run: green
            code, out, _ = run("verify.py", "run", root, "--affected", "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("SELECTED", out)
            self.assertNotEqual(run("verify.py", "status", root)[0], 0)

    def test_strict_affected_with_nothing_changed_is_not_green_either(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            code, out, _ = run("verify.py", "run", root, "--affected", "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("SELECTED", out)

    def test_name_heuristic_misses_an_imported_helper(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            write(root, "helpers/mathx.py", "def double(x):\n    return x + x\n", age=20)
            code, names = affected_names(root)
            self.assertEqual(names, [])  # the miss the coverage map exists to fix

    @unittest.skipIf(HAS_COVERAGE, "coverage.py is importable here")
    def test_record_coverage_without_coverage_says_so_and_still_runs(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            code, out, _ = run("verify.py", "run", root, "--record-coverage")
            self.assertEqual(code, 0, out)
            self.assertIn("coverage.py is not importable", out)


@unittest.skipUnless(HAS_COVERAGE, "needs coverage.py importable (pip install coverage)")
class CoverageMap(unittest.TestCase):
    def test_recorded_map_selects_the_check_that_executes_a_changed_file(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            code, out, _ = run("verify.py", "run", root, "--record-coverage", "--json")
            self.assertEqual(code, 0, out)
            self.assertEqual(json.loads(out)["summary"]["coverage_recorded"], 2)
            write(root, "helpers/mathx.py", "def double(x):\n    return x + x\n", age=20)
            code, names = affected_names(root)
            self.assertEqual((code, names), (0, ["Calc"]))
            write(root, "other.py", "def two():\n    return 1 + 1\n", age=20)
            self.assertEqual(affected_names(root)[1], ["Calc", "Other"])

    def test_map_is_shared_and_keyed_by_the_command(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            run("verify.py", "run", root, "--record-coverage")
            data = json.loads(Path(root, ".git", "verify-loop", "coverage.json").read_text())
            entry = data["Calc|python check_calc.py"]
            self.assertTrue(entry["measured"])
            self.assertIn("helpers/mathx.py", entry["files"])
            self.assertNotIn("helpers/mathx.py", data["Other|python check_other.py"]["files"])


if __name__ == "__main__":
    unittest.main()
