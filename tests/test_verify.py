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


def alive(pid):
    import subprocess, sys
    if sys.platform == "win32":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


SRV = ("import os, time\n"
       "open('pid.txt', 'w').write(str(os.getpid()))\n"
       "time.sleep(0.5)\n"
       "open('up.flag', 'w').write('1')\n"
       "time.sleep(300)\n")
UP = 'python -c "import os,sys; sys.exit(0 if os.path.exists(\'up.flag\') else 1)"'
SEEDED_AND_UP = 'python -c "import os; assert os.path.exists(\'seeded\') and os.path.exists(\'up.flag\')"'


class RunRecipe(unittest.TestCase):
    def test_setup_start_ready_then_checks_then_the_app_is_stopped(self):
        recipe = ("## Run\n"
                  "- setup: `python -c \"open('seeded', 'w').write('1')\"`\n"
                  "- start: `python srv.py`\n"
                  f"- ready: `{UP}`\n\n"
                  f"## Login\n- test: `{SEEDED_AND_UP}`\n- fail-proof: dropped the seed, went red\n\n"
                  "## Blind spots\n- none\n")
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "srv.py", SRV)
            write(tmp, "VERIFY.md", recipe)
            code, out, err = run("verify.py", "run", tmp, "--timeout", "20")
            self.assertEqual(code, 0, out + err)
            self.assertIn("PASS", out)
            self.assertIn("app ready", out)
            with open(os.path.join(tmp, "pid.txt")) as fh:
                pid = int(fh.read())
            self.assertFalse(alive(pid), "the started app must be stopped after the run")

    def test_an_app_that_never_becomes_ready_fails_and_no_check_runs(self):
        recipe = ("## Run\n"
                  "- start: `python -c \"import time; time.sleep(300)\"`\n"
                  "- ready: `python -c \"import sys; sys.exit(1)\"`\n\n"
                  "## Login\n- test: `python -c \"open('ran', 'w').write('1')\"`\n- fail-proof: x\n")
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe)
            code, out, _ = run("verify.py", "run", tmp, "--timeout", "3")
            self.assertEqual(code, 1, out)
            self.assertIn("not ready", out)
            self.assertFalse(os.path.exists(os.path.join(tmp, "ran")),
                             "checks against an app that is not up prove nothing")

    def test_a_failing_setup_stops_the_run(self):
        recipe = (f"## Run\n- setup: `{FAIL}`\n\n"
                  "## Login\n- test: `python -c \"open('ran', 'w').write('1')\"`\n- fail-proof: x\n")
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe)
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("setup failed", out)
            self.assertIn("expected 42, got 41", out)
            self.assertFalse(os.path.exists(os.path.join(tmp, "ran")))

    def test_run_checks_without_a_run_section_get_a_note(self):
        recipe = f"## Login\n- run: `{PASS}`\n- fail-proof: x\n"
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe)
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("no ## Run", out)


class Journeys(unittest.TestCase):
    BASE = (f"## Login\n- test: `{PASS}`\n- fail-proof: x\n\n"
            f"## Checkout\n- test: `{PASS}`\n- fail-proof: x\n\n")

    def test_a_journey_over_known_features_runs_and_is_counted(self):
        recipe = self.BASE + (f"## Journey: Buy something\n- features: Login, Checkout\n"
                              f"- test: `{PASS}`\n- fail-proof: x\n")
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe)
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("2 features", out)
            self.assertIn("1 journeys, 0 broken", out)

    def test_a_journey_naming_a_feature_that_has_no_section_is_broken(self):
        recipe = self.BASE + (f"## Journey: Refund it\n- features: Login, Refund\n"
                              f"- test: `{PASS}`\n- fail-proof: x\n")
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe)
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("Refund", out)
            self.assertIn("no such feature", out)
            self.assertIn("1 broken", out)

    def test_a_journey_of_fewer_than_two_features_is_broken(self):
        recipe = self.BASE + (f"## Journey: Just login\n- features: Login\n"
                              f"- test: `{PASS}`\n- fail-proof: x\n")
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", recipe)
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("fewer than two", out)


if __name__ == "__main__":
    unittest.main()
