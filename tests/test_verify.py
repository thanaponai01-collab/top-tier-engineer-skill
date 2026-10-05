#!/usr/bin/env python3
"""
verify.py — the feature-to-check map behind verify-loop.

Run them all with `python -m unittest discover tests`.
"""
from pathlib import Path
import json, os, tempfile, unittest

from _helpers import run

PASS = 'python -c "pass"'
FAIL = 'python -c "import sys; print(\'expected 42, got 41\'); sys.exit(1)"'


def write(root, rel, text=""):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


class Init(unittest.TestCase):
    def test_scaffolded_driver_is_unverified_until_real_checks_are_implemented(self):
        import subprocess, sys
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = run("verify.py", "scaffold-driver", tmp, "--type", "cli")
            self.assertEqual(code, 0, out + err)
            driver = os.path.join(tmp, "scripts", "smoke_driver.py")
            proc = subprocess.run([sys.executable, driver], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            with open(os.path.join(tmp, ".verify-evidence", "smoke_run.json"), encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["status"], "unverified")
            self.assertEqual(run("verify.py", "scaffold-driver", tmp)[0], 1)

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


class LoopMemory(unittest.TestCase):
    """The loop remembers across runs: same failure, regression, tampered check, stale green."""
    FLAG = 'python -c "import os; assert os.path.exists(\'ok.flag\'), \'missing ok.flag\'"'

    def _repo(self, tmp, cmd=None):
        write(tmp, "VERIFY.md", f"## Thing\n- test: `{cmd or self.FLAG}`\n- fail-signal: missing ok.flag\n- fail-proof: removed flag, went red\n")

    def test_same_failure_twice_says_stop_and_reobserve(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            _, out, _ = run("verify.py", "run", tmp)
            self.assertNotIn("SAME FAILURE", out)
            _, out, _ = run("verify.py", "run", tmp)
            self.assertIn("SAME FAILURE x2", out)

    def test_budget_of_red_runs_says_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            run("verify.py", "run", tmp, "--budget", "2")
            _, out, _ = run("verify.py", "run", tmp, "--budget", "2")
            self.assertIn("BUDGET  2 red runs in a row", out)

    def test_a_fix_that_breaks_a_passing_check_is_newly_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            write(tmp, "ok.flag")
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 0, out)
            os.remove(os.path.join(tmp, "ok.flag"))
            _, out, _ = run("verify.py", "run", tmp)
            self.assertIn("NEWLY RED  Thing", out)
            write(tmp, "ok.flag")
            _, out, _ = run("verify.py", "run", tmp)
            self.assertIn("NEWLY GREEN  Thing", out)

    def test_editing_a_check_after_baseline_fails_the_run_even_when_it_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, PASS)
            write(tmp, "tests/test_thing.py", "assert 1 == 2\n")
            self.assertEqual(run("verify.py", "baseline", tmp)[0], 0)
            code, out, _ = run("verify.py", "run", tmp)
            self.assertNotIn("CHECK CHANGED", out)
            write(tmp, "tests/test_thing.py", "assert True\n")
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("CHECK CHANGED  tests/test_thing.py", out)
            self.assertIn("1 checks pass, 0 fail", out)
            self.assertEqual(run("verify.py", "status", tmp)[0], 1)

    def test_only_run_does_not_touch_the_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, PASS)
            run("verify.py", "run", tmp, "--only", "thing")
            self.assertFalse(os.path.exists(os.path.join(tmp, ".verify-state.json")))

    def test_status_is_none_never_red_stale_or_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("verify.py", "status", tmp)
            self.assertEqual((code, out), (0, ""), "no VERIFY.md: not this repo's business")
            self._repo(tmp)
            code, out, _ = run("verify.py", "status", tmp)
            self.assertEqual(code, 3)
            self.assertIn("never-run", out)
            run("verify.py", "run", tmp)
            code, out, _ = run("verify.py", "status", tmp)
            self.assertEqual(code, 1)
            self.assertIn("red", out)
            write(tmp, "ok.flag")
            run("verify.py", "baseline", tmp)
            run("verify.py", "run", tmp, "--strict")
            code, out, _ = run("verify.py", "status", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("green", out)
            write(tmp, "src/app.py", "x = 1\n")
            code, out, _ = run("verify.py", "status", tmp)
            self.assertEqual(code, 3)
            self.assertIn("stale", out)


class EvidenceGate(unittest.TestCase):
    CHECK = 'python check.py'

    def _repo(self, tmp):
        write(tmp, "check.py", "assert open('value.txt').read() == '42', 'expected 42'\n")
        write(tmp, "value.txt", "41")
        write(tmp, "VERIFY.md", "## Answer\n- test: `python check.py`\n"
              "- oracle: check.py\n- fail-signal: expected 42\n- fail-proof: input 41 rejected, expected 42\n")

    def test_undeclared_direct_helper_cannot_be_replaced_with_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            recipe = Path(tmp, "VERIFY.md")
            recipe.write_text(recipe.read_text().replace("- oracle: check.py\n", ""))
            self.assertEqual(run("verify.py", "run", tmp)[0], 1)
            self.assertEqual(run("verify.py", "baseline", tmp)[0], 0)
            write(tmp, "check.py", "pass\n")
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("CHECK CHANGED", out)
            self.assertEqual(Path(tmp, "value.txt").read_text(), "41")

    def test_dependency_failure_cannot_prove_product_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            write(tmp, "check.py", "from pathlib import Path\n"
                  "if not Path('dependency.ready').exists(): raise SystemExit('missing dependency')\n")
            self.assertEqual(run("verify.py", "run", tmp)[0], 1)
            run("verify.py", "baseline", tmp)
            write(tmp, "dependency.ready", "ready")
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("no recorded failing run", out)

    def test_matching_harness_error_still_cannot_prove_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            recipe = Path(tmp, "VERIFY.md")
            recipe.write_text(recipe.read_text().replace("fail-signal: expected 42", "fail-signal: missing dependency"))
            write(tmp, "check.py", "from pathlib import Path\n"
                  "if not Path('dependency.ready').exists(): raise SystemExit('missing dependency')\n")
            run("verify.py", "run", tmp)
            run("verify.py", "baseline", tmp)
            write(tmp, "dependency.ready", "ready")
            self.assertEqual(run("verify.py", "run", tmp, "--strict")[0], 1)

    def test_prose_alone_cannot_pass_strict_and_status_keeps_the_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", f"## Answer\n- test: `{PASS}`\n- fail-proof: claimed red\n")
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("no recorded failing run", out)
            self.assertEqual(run("verify.py", "status", tmp)[0], 1)

    def test_a_non_strict_pass_is_partial_not_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", f"## Answer\n- test: `{PASS}`\n- fail-proof: x\n")
            self.assertEqual(run("verify.py", "run", tmp)[0], 0)
            code, out, _ = run("verify.py", "status", tmp)
            self.assertEqual(code, 3, out)
            self.assertIn("partial", out)

    def test_missing_oracle_is_a_failure_even_after_a_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            run("verify.py", "baseline", tmp)
            os.remove(os.path.join(tmp, "check.py"))
            code, out, err = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out + err)
            self.assertIn("invalid oracle", out)
            self.assertEqual(run("verify.py", "status", tmp)[0], 1)

    def test_strict_missing_proof_and_unverified_features_stay_red(self):
        for extra in ("", "\n## Not checked\n"):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as tmp:
                write(tmp, "VERIFY.md", f"## Answer\n- test: `{PASS}`\n" + extra)
                self.assertEqual(run("verify.py", "run", tmp, "--strict")[0], 1)
                self.assertEqual(run("verify.py", "status", tmp)[0], 1)

    def test_real_red_then_green_records_output_and_freezes_the_oracle(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            self.assertEqual(run("verify.py", "run", tmp)[0], 1)
            write(tmp, "value.txt", "42")
            self.assertEqual(run("verify.py", "baseline", tmp)[0], 0)
            code, out, err = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 0, out + err)
            self.assertEqual(run("verify.py", "status", tmp)[0], 0)
            with open(os.path.join(tmp, ".verify-state.json"), encoding="utf-8") as fh:
                state = json.load(fh)
            proof = state["failures"]["Answer|python check.py"]
            self.assertIn("expected 42", proof["output"])
            self.assertEqual(proof["exit"], 1)
            write(tmp, "check.py", "pass\n")
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("CHECK CHANGED  check.py", out)

    def test_editing_the_check_invalidates_its_old_failure_even_without_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            run("verify.py", "run", tmp)
            write(tmp, "check.py", "pass\n")
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("no recorded failing run", out)

    def test_a_check_cannot_rewrite_its_oracle_and_leave_a_valid_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            write(tmp, "check.py", "open('check.py', 'w').write('pass\\n')\n"
                  "raise AssertionError('wrong result')\n")
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("CHECK CHANGED DURING RUN", out)
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("no recorded failing run", out)

    def test_oracle_removed_during_the_check_fails_without_a_traceback_from_the_runner(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            write(tmp, "check.py", "from pathlib import Path\nPath('check.py').unlink()\n")
            code, out, err = run("verify.py", "run", tmp)
            self.assertEqual(code, 1, out + err)
            self.assertIn("CHECK CHANGED DURING RUN", out)
            self.assertEqual(err, "")

    def test_doctor_failure_prevents_checks_and_invalidates_previous_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", f"## Answer\n- test: `{PASS}`\n- fail-proof: x\n"
                  "\n## Run\n- doctor: `python doctor.py`\n")
            write(tmp, "doctor.py", "pass\n")
            self.assertEqual(run("verify.py", "run", tmp)[0], 0)
            write(tmp, "doctor.py", "raise SystemExit('wrong build')\n")
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("doctor failed", out)
            self.assertNotIn("  PASS", out)
            self.assertEqual(run("verify.py", "status", tmp)[0], 1)

    def test_status_detects_same_size_content_change_even_with_restored_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            write(tmp, "value.txt", "42")
            run("verify.py", "run", tmp)
            path = os.path.join(tmp, "value.txt")
            stat = os.stat(path)
            write(tmp, "value.txt", "41")
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            self.assertEqual(run("verify.py", "status", tmp)[0], 3)


class Scope(unittest.TestCase):
    """The fix may touch what it named. Editing anything else, or breaking what worked, is visible."""
    CHECK = 'python -c "import sys; sys.exit(\'bad\' in open(\'good.txt\').read())"'

    def _repo(self, tmp):
        write(tmp, "VERIFY.md", f"## Thing\n- test: `{self.CHECK}`\n- fail-proof: wrote bad, went red\n")
        write(tmp, "good.txt", "ok")
        write(tmp, "other.txt", "untouched")
        write(tmp, "src/a.py", "x = 1")
        self.assertEqual(run("verify.py", "run", tmp)[0], 0)

    def test_edit_outside_the_scope_fails_run_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            code, out, _ = run("verify.py", "scope", "src/", "--repo", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("keep-green: 1 check(s)", out)
            write(tmp, "src/a.py", "x = 2")
            self.assertEqual(run("verify.py", "run", tmp)[0], 0, "an edit inside the scope is fine")
            write(tmp, "other.txt", "re-edited")
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("OUT OF SCOPE  other.txt", out)
            code, out, _ = run("verify.py", "status", tmp)
            self.assertEqual(code, 1)
            self.assertIn("out-of-scope", out)

    def test_widening_is_explicit_and_clear_drops_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            run("verify.py", "scope", "src/", "--repo", tmp)
            write(tmp, "other.txt", "re-edited")
            self.assertEqual(run("verify.py", "scope", "--check", "--repo", tmp)[0], 1)
            self.assertEqual(run("verify.py", "scope", "other.txt", "--add", "--repo", tmp)[0], 0)
            self.assertEqual(run("verify.py", "run", tmp)[0], 0)
            run("verify.py", "scope", "--clear", "--repo", tmp)
            write(tmp, "src/new.py", "y")
            self.assertEqual(run("verify.py", "run", tmp)[0], 0)

    def test_added_and_deleted_files_count_as_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            run("verify.py", "scope", "src/", "--repo", tmp)
            os.remove(os.path.join(tmp, "other.txt"))
            write(tmp, "extra.txt", "new")
            _, out, _ = run("verify.py", "scope", "--check", "--repo", tmp)
            self.assertIn("OUT OF SCOPE  other.txt", out)
            self.assertIn("OUT OF SCOPE  extra.txt", out)

    def test_working_checks_stay_on_watch_every_run_not_only_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            run("verify.py", "scope", "good.txt", "--repo", tmp)
            write(tmp, "good.txt", "bad")
            _, out, _ = run("verify.py", "run", tmp)
            self.assertIn("KEEP-GREEN BROKEN  Thing", out)
            write(tmp, "good.txt", "bad again")
            code, out, _ = run("verify.py", "run", tmp)
            self.assertEqual(code, 1)
            self.assertNotIn("NEWLY RED", out, "second red run is not newly red")
            self.assertIn("KEEP-GREEN BROKEN  Thing", out, "but it must still be called out")

    def test_scope_without_a_passing_run_says_nothing_is_on_watch(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", f"## Thing\n- test: `{self.CHECK}`\n")
            write(tmp, "good.txt", "ok")
            _, out, _ = run("verify.py", "scope", "good.txt", "--repo", tmp)
            self.assertIn("no passing run on record", out)


class TestMap(unittest.TestCase):
    """`verify.py tests`: every test function under the feature whose command names its file,
    and the ones that can never go red flagged. Static: it runs no check."""

    CART = (
        "import unittest\n\n\n"
        "def check_total(t, expected):\n    assert t == expected\n\n\n"
        "class Cart(unittest.TestCase):\n"
        "    def test_real(self):\n        self.assertEqual(1 + 1, 2)\n\n"
        "    def test_no_assert(self):\n        x = 1 + 1\n\n"
        "    def test_helper_asserts(self):\n        check_total(2, 2)\n\n"
        "    def test_swallow(self):\n        try:\n            int('x')\n"
        "        except ValueError:\n            pass\n\n"
        "    def test_raises_ok(self):\n        with self.assertRaises(ValueError):\n            int('x')\n\n"
        "    @unittest.skip('later')\n    def test_skipped(self):\n        self.assertTrue(True)\n\n\n"
        "def test_module_level_style():\n    assert True\n"
    )
    ONE = "import unittest\nclass R(unittest.TestCase):\n    def test_refund(self):\n        self.assertTrue(1)\n"
    LONELY = ("import unittest\nclass L(unittest.TestCase):\n"
              "    def test_a(self):\n        self.assertTrue(1)\n    def test_b(self):\n        pass\n")
    RECIPE = (f"## Cart\n- test: `{PASS} tests/test_cart.py`\n- fail-proof: x\n\n"
              f"## Refunds\n- test: `{PASS} tests/test_refunds.py`\n- fail-proof: x\n")

    def _repo(self, tmp):
        write(tmp, "VERIFY.md", self.RECIPE)
        write(tmp, "tests/test_cart.py", self.CART)
        write(tmp, "tests/test_refunds.py", self.ONE)
        write(tmp, "tests/test_lonely.py", self.LONELY)

    @staticmethod
    def _line(out, name):
        hits = [ln for ln in out.splitlines() if ln.rstrip().split("  <- ")[0].endswith(name)]
        assert len(hits) == 1, (name, hits)
        return hits[0]

    def test_every_test_is_listed_under_the_feature_that_names_its_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            code, out, _ = run("verify.py", "tests", tmp)
            self.assertEqual(code, 0)
            cart = out[out.index("\nCart\n"):out.index("\nRefunds\n")]
            for name in ("Cart.test_real", "Cart.test_no_assert", "Cart.test_helper_asserts",
                         "Cart.test_swallow", "Cart.test_raises_ok", "Cart.test_skipped",
                         "test_module_level_style"):
                self.assertIn(name, cart)
            self.assertIn("R.test_refund", out[out.index("\nRefunds\n"):out.index("Unmapped")])

    def test_tests_that_cannot_fail_are_flagged_and_the_decoys_are_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            _, out, _ = run("verify.py", "tests", tmp)
            self.assertIn("no assertion", self._line(out, "Cart.test_no_assert"))
            self.assertIn("passes either way", self._line(out, "Cart.test_swallow"))
            self.assertIn("skipped", self._line(out, "Cart.test_skipped"))
            for decoy in ("Cart.test_real", "Cart.test_helper_asserts", "Cart.test_raises_ok",
                          "test_module_level_style"):
                self.assertNotIn("<-", self._line(out, decoy), decoy)

    def test_tests_in_a_file_no_feature_names_are_unmapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            _, out, _ = run("verify.py", "tests", tmp)
            block = out.split("Unmapped")[1]
            self.assertIn("test_lonely.py::L.test_a", block)
            self.assertIn("test_lonely.py::L.test_b", block)
            self.assertNotIn("test_cart.py", block)

    def test_the_summary_line_counts_each_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            _, out, _ = run("verify.py", "tests", tmp)
            self.assertIn("TESTS: 10 tests | 8 mapped to a feature | 2 unmapped | "
                          "3 without an assertion or a way to fail | 1 skipped", out)

    def test_strict_fails_on_a_test_that_cannot_fail_or_has_no_feature(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            self.assertEqual(run("verify.py", "tests", tmp, "--strict")[0], 1)
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "VERIFY.md", self.RECIPE)
            write(tmp, "tests/test_cart.py", "def test_ok():\n    assert 1\n")
            write(tmp, "tests/test_refunds.py", self.ONE)
            self.assertEqual(run("verify.py", "tests", tmp, "--strict")[0], 0)

    def test_strict_fails_on_skipped_or_unparseable_tests(self):
        for text in ("import unittest\n@unittest.skip('later')\ndef test_ok():\n    assert 1\n",
                     "def test_broken(:\n    pass\n"):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                write(tmp, "VERIFY.md", self.RECIPE)
                write(tmp, "tests/test_cart.py", text)
                self.assertEqual(run("verify.py", "tests", tmp, "--strict")[0], 1)

    def test_no_recipe_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run("verify.py", "tests", tmp)[0], 2)


if __name__ == "__main__":
    unittest.main()
