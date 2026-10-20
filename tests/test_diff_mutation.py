"""1.11.0: `challenge --auto --diff [REF]` mutates only the lines a change touched, in one named
file or in every changed product file, on the same lanes as a whole-file survey.

Run with: python -m unittest discover tests
"""
import json, subprocess, tempfile, unittest
from pathlib import Path

from _helpers import run

GRADE = ("def grade(score):\n    if score >= 50:\n        return 'pass'\n    return 'fail'\n")
BONUS = ("\n\ndef bonus(score):\n    if score > 90:\n        return 5\n    return 0\n")


def git(root, *args):
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True)


def committed(root):
    Path(root, "app.py").write_text(GRADE)
    Path(root, "test_app.py").write_text(
        "from app import grade, bonus\n"
        "assert grade(50) == 'pass' and grade(49) == 'fail', 'expected grade boundary at 50'\n"
        "assert bonus(95) == 5 and bonus(91) == 5, 'expected bonus 5 above 90'\n"
        "assert bonus(90) == 0 and bonus(10) == 0, 'expected bonus 0 at or below 90'\n")
    Path(root, "VERIFY.md").write_text("## Grade\n- test: `python test_app.py`\n- fail-signal: expected\n")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x")
    Path(root, "app.py").write_text(GRADE + BONUS)  # the change: lines 5-10 are new


def auto(root, *args):
    code, out, err = run("verify.py", "challenge", root, "--feature", "Grade", "--json", *args)
    return code, (json.loads(out) if out.strip().startswith("{") else out + err)


class DiffScopedMutation(unittest.TestCase):
    def test_only_lines_changed_since_head_are_mutated(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            code, s = auto(root, "--auto", "app.py", "--diff")
            self.assertEqual(code, 0, s)
            self.assertTrue(s["results"])
            self.assertTrue(all(r["line"] >= 7 for r in s["results"]), s["results"])
            self.assertEqual(s["diff"], "HEAD")
            _, whole = auto(root, "--auto", "app.py")
            self.assertTrue(any(r["line"] < 5 for r in whole["results"]))

    def test_without_a_file_every_changed_product_file_is_mutated_and_checks_are_not(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "extra.py").write_text("LIMIT = 3\n")  # untracked: every line is new
            code, s = auto(root, "--auto", "--diff", "HEAD")
            self.assertEqual(sorted(s["files"]), ["app.py", "extra.py"], s)
            self.assertTrue({r["file"] for r in s["results"]} <= {"app.py", "extra.py"})
            self.assertTrue(any(r["file"] == "extra.py" for r in s["results"]))
            self.assertEqual(Path(root, "app.py").read_text(), GRADE + BONUS)

    def test_a_change_with_no_mutable_line_is_not_a_score(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            git(root, "add", "-A")
            git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "y")
            Path(root, "app.py").write_text(GRADE + BONUS + "# a comment\n")
            code, out, err = run("verify.py", "challenge", root, "--feature", "Grade", "--auto", "app.py", "--diff")
            self.assertEqual(code, 2, out + err)
            self.assertIn("no mutable lines changed", out)

    def test_diff_against_an_older_ref(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            git(root, "add", "-A")
            git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "bonus")
            code, s = auto(root, "--auto", "app.py", "--diff", "HEAD~1")
            self.assertTrue(s["results"] and all(r["line"] >= 7 for r in s["results"]), s)

    def test_diff_needs_auto(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            code, out, err = run("verify.py", "challenge", root, "--feature", "Grade", "--diff")
            self.assertEqual(code, 2, out + err)


if __name__ == "__main__":
    unittest.main()
