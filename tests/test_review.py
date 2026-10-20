"""1.13.0: `review [--base REF]` turns a change review into findings with proof: tests and checks the
change weakened, and changed lines no check catches or reaches. It reads; it never edits or records.

Run with: python -m unittest discover tests
"""
import json, subprocess, tempfile, unittest
from pathlib import Path

from _helpers import run

GRADE = "def grade(score):\n    if score >= 50:\n        return 'pass'\n    return 'fail'\n"
BONUS = "\n\ndef bonus(score):\n    if score > 90:\n        return 5\n    return 0\n"
TESTS = ("import unittest\nfrom app import grade\n\n\nclass T(unittest.TestCase):\n"
         "    def test_boundary(self):\n"
         "        self.assertEqual(grade(50), 'pass', 'expected pass at 50')\n"
         "        self.assertEqual(grade(49), 'fail', 'expected fail at 49')\n\n"
         "    def test_low(self):\n"
         "        self.assertEqual(grade(0), 'fail', 'expected fail at 0')\n\n"
         "    def test_high(self):\n"
         "        self.assertEqual(grade(100), 'pass', 'expected pass at 100')\n")
BONUS_TESTS = ("\n\nfrom app import bonus\n\n\nclass B(unittest.TestCase):\n"
               "    def test_bonus(self):\n"
               "        self.assertEqual(bonus(91), 5, 'expected 5 above 90')\n"
               "        self.assertEqual(bonus(95), 5, 'expected 5 above 90')\n"
               "        self.assertEqual(bonus(90), 0, 'expected 0 at 90')\n"
               "        self.assertEqual(bonus(10), 0, 'expected 0 below 90')\n")
RECIPE = ("## Grade\n- test: `python -m unittest -q test_app`\n- fail-signal: expected\n\n"
          "## Prices\n- test: `python check_prices.py`\n- oracle: prices.json\n- fail-signal: expected\n")


def git(root, *args):
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True)


def committed(root):
    Path(root, "app.py").write_text(GRADE)
    Path(root, "test_app.py").write_text(TESTS)
    Path(root, "prices.json").write_text('{"tea": 3}\n')
    Path(root, "check_prices.py").write_text(
        "import json\nassert json.load(open('prices.json'))['tea'] > 0, 'expected a tea price'\n")
    Path(root, "VERIFY.md").write_text(RECIPE)
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")


def review(root, *args):
    code, out, err = run("verify.py", "review", root, "--json", *args)
    return code, (json.loads(out) if out.strip().startswith("{") else out + err)


def kinds(s):
    return sorted(f["kind"] for f in s["findings"])


class ReviewByProof(unittest.TestCase):
    def test_a_tested_change_has_no_findings(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "app.py").write_text(GRADE + BONUS)
            Path(root, "test_app.py").write_text(TESTS + BONUS_TESTS)
            code, s = review(root)
            self.assertEqual(code, 0, s)
            self.assertEqual(s["findings"], [])
            self.assertEqual(s["base"], "HEAD")
            self.assertGreater(s["mutation"]["caught"], 0)

    def test_weakened_skipped_and_removed_tests_are_findings(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            weak = (TESTS.replace("        self.assertEqual(grade(49), 'fail', 'expected fail at 49')\n", "")
                         .replace("    def test_low", "    @unittest.skip('later')\n    def test_low")
                         .split("    def test_high")[0])
            Path(root, "test_app.py").write_text(weak)
            code, s = review(root, "--no-mutate")
            self.assertEqual(code, 1, s)
            self.assertEqual(kinds(s), ["TEST REMOVED", "TEST SKIPPED", "TEST WEAKENED"])
            weakened = next(f for f in s["findings"] if f["kind"] == "TEST WEAKENED")
            self.assertEqual(weakened["file"], "test_app.py")
            self.assertIn("T.test_boundary", weakened["detail"])
            self.assertIn("2 -> 1", weakened["detail"])
            self.assertTrue(all(f["severity"] == "high" for f in s["findings"]))

    def test_a_deleted_test_file_removes_its_tests(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "test_app.py").unlink()
            code, s = review(root, "--no-mutate")
            self.assertEqual(kinds(s), ["TEST REMOVED"] * 3, s)

    def test_check_signal_and_oracle_edits_are_findings(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "VERIFY.md").write_text(
                RECIPE.replace("- fail-signal: expected\n\n", "- fail-signal: Error\n\n", 1)
                      .replace("- test: `python check_prices.py`\n", ""))
            Path(root, "prices.json").write_text('{"tea": 4}\n')
            code, s = review(root, "--no-mutate")
            self.assertEqual(code, 1, s)
            self.assertEqual(kinds(s), ["CHECK REMOVED", "ORACLE CHANGED", "SIGNAL CHANGED"])

    def test_untested_changed_lines_are_findings_with_a_command_to_reproduce(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "app.py").write_text(GRADE + BONUS)  # no test reaches bonus()
            code, s = review(root)
            self.assertEqual(code, 1, s)
            found = [f for f in s["findings"] if f["kind"] == "UNCOVERED"]
            self.assertTrue(found, s)
            self.assertTrue(all(f["file"] == "app.py" and f["line"] >= 7 for f in found), found)
            self.assertTrue(all(f["severity"] == "medium" for f in found))
            self.assertIn("challenge", found[0]["reproduce"])
            self.assertNotIn("TEST REMOVED", kinds(s))

    def test_a_weak_check_lets_a_mutant_survive(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "app.py").write_text(GRADE + BONUS)
            Path(root, "test_app.py").write_text(TESTS + BONUS_TESTS.replace(
                "        self.assertEqual(bonus(90), 0, 'expected 0 at 90')\n", ""))
            code, s = review(root)
            self.assertEqual(code, 1, s)
            self.assertIn("SURVIVED", kinds(s))

    def test_a_changed_file_no_feature_reaches_is_unmapped(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "notes.md").write_text("docs are not product code\n")
            Path(root, "limits.py").write_text("LIMIT = 3\n")
            code, s = review(root, "--no-mutate")
            self.assertEqual([(f["kind"], f["file"]) for f in s["findings"]], [("UNMAPPED", "limits.py")], s)

    def test_review_reads_and_never_writes(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "app.py").write_text(GRADE + BONUS)
            before = {p.name: p.read_bytes() for p in Path(root).iterdir() if p.is_file()}
            review(root)
            after = {p.name: p.read_bytes() for p in Path(root).iterdir() if p.is_file()}
            self.assertEqual(before, after)

    def test_text_output_ranks_findings_and_names_the_verdict(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "app.py").write_text(GRADE + BONUS)
            Path(root, "test_app.py").write_text(TESTS.split("    def test_high")[0])
            code, out, err = run("verify.py", "review", root)
            self.assertEqual(code, 1, out + err)
            lines = [l for l in out.splitlines() if l.startswith(("  HIGH", "  MEDIUM"))]
            self.assertTrue(lines[0].startswith("  HIGH  TEST REMOVED"), out)
            self.assertTrue(lines[-1].startswith("  MEDIUM"), out)
            self.assertIn("REVIEW:", out)
            self.assertIn("VERIFY-STATE:", out)

    def test_without_a_recipe_one_finding_says_nothing_judges_the_change(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            Path(root, "VERIFY.md").unlink()
            git(root, "add", "-A")
            git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "no recipe")
            Path(root, "app.py").write_text(GRADE + BONUS)
            Path(root, "limits.py").write_text("LIMIT = 3\n")
            code, s = review(root)
            self.assertEqual(code, 1, s)
            self.assertEqual(kinds(s), ["NOT SURVEYED"])
            self.assertIn("2 changed product file(s)", s["findings"][0]["detail"])

    def test_a_bad_base_cannot_be_reviewed(self):
        with tempfile.TemporaryDirectory() as root:
            committed(root)
            code, out, err = run("verify.py", "review", root, "--base", "no-such-ref")
            self.assertEqual(code, 2, out + err)


if __name__ == "__main__":
    unittest.main()
