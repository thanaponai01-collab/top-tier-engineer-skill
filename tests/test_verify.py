#!/usr/bin/env python3
"""
verify.py — the feature-to-check map behind verify-loop.

Run them all with `python -m unittest discover tests`.
"""
import os, tempfile, unittest

from _helpers import run

PASS = 'python -c "pass"'
FAIL = 'python -c "import sys; print(\'expected 42, got 41\'); sys.exit(1)"'


def write(root, rel, text=""):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


class Init(unittest.TestCase):
    def test_drafts_one_feature_per_test_file_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "tests/test_cart.py")
            write(tmp, "tests/test_auth.py")
            write(tmp, "node_modules/x/test_junk.py")
            code, out, err = run("verify.py", "init", tmp)
            self.assertEqual(code, 0, err)
            with open(os.path.join(tmp, "VERIFY.md"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("## Cart", text)
            self.assertIn("## Auth", text)
            self.assertNotIn("Junk", text)
            self.assertIn("python -m unittest discover -s tests -p test_cart.py", text)
            code, out, _ = run("verify.py", "init", tmp)
            self.assertEqual(code, 2)
            self.assertIn("not overwriting", out)

    def test_a_draft_is_not_a_verified_recipe(self):
        """TODO placeholders must not count as a proof, or init would hand out a green it never earned."""
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "tests/test_cart.py", "import unittest\nclass T(unittest.TestCase):\n    def test_a(self): pass\n")
            run("verify.py", "init", tmp)
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("1 unproven", out)
            self.assertIn("PASS", out)

    def test_no_tests_still_writes_a_skeleton(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("verify.py", "init", tmp)
            self.assertEqual(code, 0)
            self.assertIn("No tests found", out)


class Run(unittest.TestCase):
    RECIPE = f"""# VERIFY

## Login
- test: `{PASS}`
- fail-proof: broke the password check, test went red, reverted

## Checkout
- test: `{FAIL}`
- fail-proof: n/a

## Export
- (nothing yet)

## Blind spots
- payment gateway is stubbed
"""

    def _repo(self, tmp, recipe=None):
        write(tmp, "VERIFY.md", recipe or self.RECIPE)

    def test_failure_shows_the_specific_signal_and_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 1)
            self.assertIn("FAIL", out)
            self.assertIn("expected 42, got 41", out)
            self.assertIn("(exit 1)", out)

    def test_green_run_still_names_what_it_does_not_cover(self):
        recipe = f"## Login\n- test: `{PASS}`\n- fail-proof: broke it, went red\n\n## Export\n\n## Blind spots\n- gateway stubbed\n"
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, recipe)
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("UNVERIFIED  no checks", out)
            self.assertIn("gateway stubbed", out)
            self.assertIn("1 unverified", out)
            code, _, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, "--strict must refuse a green that hides an unverified feature")

    def test_check_with_no_fail_proof_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, f"## Login\n- test: `{PASS}`\n")
            _, out, _ = run("verify.py", "run", tmp)
            self.assertIn("no fail-proof recorded", out)
            self.assertIn("1 unproven", out)

    def test_orphans_are_test_files_no_command_names(self):
        """tests/test_cart.py is named by path, tests/unit/ by directory; test_lonely.py by nothing.
        The decoys: tests/a_test.py is a suffix of the covered data_test.py and must stay an orphan."""
        recipe = (f"## Cart\n- test: `{PASS} tests/test_cart.py`\n- fail-proof: x\n\n"
                  f"## Unit\n- test: `{PASS} tests/unit/`\n- fail-proof: x\n\n"
                  f"## Data\n- test: `{PASS} tests/data_test.py`\n- fail-proof: x\n")
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, recipe)
            for rel in ("tests/test_cart.py", "tests/unit/test_a.py", "tests/test_lonely.py",
                        "tests/test_mycart.py", "tests/data_test.py", "tests/a_test.py"):
                write(tmp, rel)
            _, out, _ = run("verify.py", "run", tmp)
            orphan_block = out.split("Orphan tests")[1]
            self.assertIn("tests/test_lonely.py", orphan_block)
            self.assertIn("tests/test_mycart.py", orphan_block)
            self.assertIn("tests/a_test.py", orphan_block)
            self.assertNotIn("tests/data_test.py", orphan_block)
            self.assertNotIn("tests/test_cart.py", orphan_block)
            self.assertNotIn("tests/unit/test_a.py", orphan_block)
            self.assertIn("3 orphan tests", out)

    def test_only_filters_features(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            code, out, _ = run("verify.py", "run", tmp, "--only", "login")
            self.assertEqual(code, 0, out)
            self.assertNotIn("Checkout", out)

    def test_timeout_is_a_failure_not_a_hang(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, '## Slow\n- test: `python -c "import time; time.sleep(3)"`\n- fail-proof: x\n')
            code, out, _ = run("verify.py", "run", tmp, "--timeout", "1")
            self.assertEqual(code, 1)
            self.assertIn("timed out after 1s", out)

    def test_missing_or_empty_recipe_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 2)
            self.assertIn("verify.py init", out)
            write(tmp, "VERIFY.md", "# VERIFY\nnothing here\n")
            code, _, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
