"""The gates: rules that used to be prose in SKILL.md, now verdicts the helper prints."""
import json, os, subprocess, tempfile, unittest

from _helpers import run

GOOD = "def total(a, b):\n    return a + b\n"
BAD = "def total(a, b):\n    return a + b + 1\n"
TEST = ("import unittest\n\nfrom calc import total\n\n\nclass T(unittest.TestCase):\n"
        "    def test_total(self):\n        self.assertEqual(total(40, 2), 42, 'expected total 42')\n")


def write(root, rel, text=""):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def git(root, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="dev", GIT_AUTHOR_EMAIL="dev@example.invalid",
               GIT_COMMITTER_NAME="dev", GIT_COMMITTER_EMAIL="dev@example.invalid")
    return subprocess.run(["git", "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *args],
                          cwd=root, env=env, capture_output=True, text=True, check=True).stdout


def recipe(signal="expected total 42", extra=""):
    return ("## Total\n- path: calc.py\n- test: `python -m unittest test_calc.py`\n"
            f"- fail-signal: {signal}\n- fail-proof: total adds one, test went red, restored\n{extra}")


def project(root, signal="expected total 42", extra=""):
    write(root, "calc.py", GOOD)
    write(root, "test_calc.py", TEST)
    write(root, "VERIFY.md", recipe(signal, extra))


def prove(root):
    """The prove step done right: wrong product, run, restore, freeze, strict run."""
    write(root, "calc.py", BAD)
    run("verify.py", "run", root)
    write(root, "calc.py", GOOD)
    run("verify.py", "baseline", root)
    return run("verify.py", "run", root, "--strict")


def report(root):
    return json.loads(run("verify.py", "report", root, "--json")[1])


class Baseline(unittest.TestCase):
    def test_the_prove_step_done_right_is_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            code, out, _ = prove(tmp)
            self.assertEqual(code, 0, out)
            a = report(tmp)
            self.assertEqual(a["verdict"], "green", a)
            for key in ("unmapped", "weak_signal", "loosened", "blocked", "proof_not_from_product"):
                self.assertEqual(a["gaps"][key], [], key)


class AnswerCheck(unittest.TestCase):
    def check(self, root, text):
        with tempfile.TemporaryDirectory() as out_dir:  # outside the repo: writing it must not make the tree stale
            path = os.path.join(out_dir, "answer.md")
            write(out_dir, "answer.md", text)
            code, out, _ = run("verify.py", "answer-check", root, "--answer", path, "--json")
        return code, json.loads(out)

    def test_a_green_answer_that_says_so_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            prove(tmp)
            code, a = self.check(tmp, "VERDICT: green. Total is verified: calc.py rejected total+1.\n")
            self.assertEqual((code, a["problems"]), (0, []), a)

    def test_no_verdict_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            prove(tmp)
            code, a = self.check(tmp, "Looks fine to me.\n")
            self.assertEqual(code, 1)
            self.assertEqual(a["problems"][0]["kind"], "NO VERDICT")

    def test_claiming_done_on_a_red_state_is_an_overclaim(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "calc.py", BAD)
            run("verify.py", "run", tmp)
            code, a = self.check(tmp, "**Verdict: red** for Total, but it is ready to merge.\n")
            self.assertEqual(code, 1)
            self.assertIn("OVERCLAIM", [p["kind"] for p in a["problems"]])

    def test_a_negated_claim_is_not_an_overclaim(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "calc.py", BAD)
            run("verify.py", "run", tmp)
            code, a = self.check(tmp, "Verdict: red. Total fails; this is not ready to merge.\n")
            self.assertEqual((code, a["problems"]), (0, []), a)

    def test_every_gap_must_be_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp, extra="\n## Blind spots\n- the payment gateway is stubbed\n")
            write(tmp, "search.py", "def search(q):\n    return []\n")
            prove(tmp)
            code, a = self.check(tmp, "Verdict: red. Total passes.\n")
            self.assertEqual(code, 1)
            details = [p["detail"] for p in a["problems"]]
            self.assertIn("unmapped: search.py", details)
            self.assertIn("blind spot: the payment gateway is stubbed", details)
            code, a = self.check(tmp, "Verdict: red. search.py has no check; the payment gateway is stubbed.\n")
            self.assertEqual((code, a["problems"]), (0, []), a)

    def test_a_name_inside_another_word_does_not_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "calc.py", BAD)
            run("verify.py", "run", tmp)
            code, a = self.check(tmp, "Verdict: red. In totality the work went fine.\n")
            self.assertEqual(code, 1)
            self.assertIn("failing: Total", [p["detail"] for p in a["problems"]])


class Unmapped(unittest.TestCase):
    def test_product_code_nothing_reaches_keeps_strict_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "search.py", "def search(q):\n    return []\n")
            code, out, _ = prove(tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("UNMAPPED  search.py", out)
            self.assertEqual(report(tmp)["gaps"]["unmapped"], ["search.py"])

    def test_a_blind_spot_naming_it_clears_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp, extra="\n## Blind spots\n- `legacy/` is frozen and untested\n")
            write(tmp, "legacy/search.py", "def search(q):\n    return []\n")
            code, out, _ = prove(tmp)
            self.assertEqual(code, 0, out)

    def test_code_a_checked_test_imports_is_reached(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "util/money.py", "def cents(x):\n    return int(x * 100)\n")
            write(tmp, "calc.py", "from util.money import cents\n\n" + BAD)
            run("verify.py", "run", tmp)
            write(tmp, "calc.py", "from util.money import cents\n\n" + GOOD)
            run("verify.py", "baseline", tmp)
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 0, out)
            self.assertNotIn("UNMAPPED", out)

    def test_a_same_named_file_in_a_subfolder_does_not_map_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "tools/app.py", "def main():\n    return 0\n")
            write(tmp, "app.py", "def serve():\n    return 1\n")
            write(tmp, "VERIFY.md", recipe().replace("python -m unittest test_calc.py",
                                                     "python tools/app.py && python -m unittest test_calc.py"))
            code, out, _ = run("verify.py", "run", tmp)
            self.assertIn("UNMAPPED  app.py", out)
            self.assertNotIn("UNMAPPED  tools/app.py", out)

    def test_constants_and_empty_init_are_not_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "pkg/__init__.py", "")
            write(tmp, "settings.py", "DEBUG = False\n")
            code, out, _ = prove(tmp)
            self.assertEqual(code, 0, out)


class WeakSignal(unittest.TestCase):
    def test_boilerplate_signal_proves_nothing(self):
        for signal in ("AssertionError", "FAILED", "Error", "[FAIL] or [ERR]", "exit code 1"):
            with self.subTest(signal=signal), tempfile.TemporaryDirectory() as tmp:
                project(tmp, signal=signal)
                code, out, _ = prove(tmp)
                self.assertEqual(code, 1, out)
                self.assertIn("WEAK SIGNAL", out)
                self.assertTrue(report(tmp)["gaps"]["weak_signal"])

    def test_a_signal_naming_a_value_or_behavior_is_enough(self):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "skills", "verify-loop", "scripts"))
        import gates
        for signal in ("expected 42", "expected total 42", "NOTES_FAIL", "refund credit mismatch",
                       "expected status 200, got 500", "SchemaValidationError", "expected status 200",
                       "expected code 404"):
            self.assertIsNone(gates.weak_signal(signal), signal)
        for signal in ("AssertionError:", "FAILED", "[UI FAIL]", "not ok", "expected", "Traceback",
                       "exit code 1", "exited with status 2", "1 failed", "Error at line 12"):
            self.assertTrue(gates.weak_signal(signal), signal)


class WhereTheWrongStateWas(unittest.TestCase):
    def test_a_red_from_the_environment_is_not_a_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            check = ("import os, sys\nfrom calc import total\n"
                     "ok = total(40, 2) == 42 and not os.environ.get('BREAK')\n"
                     "sys.exit(0 if ok else (print('expected total 42') or 1))\n")
            write(tmp, "check_calc.py", check)
            write(tmp, "VERIFY.md", recipe().replace("python -m unittest test_calc.py",
                                                     "python check_calc.py && python -m unittest test_calc.py"))
            env = dict(os.environ, BREAK="1")
            subprocess.run([__import__("sys").executable, os.path.join(
                os.path.dirname(__file__), "..", "plugin", "skills", "verify-loop", "scripts", "verify.py"),
                "run", tmp], env=env, capture_output=True)
            run("verify.py", "baseline", tmp)
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("PROOF NOT FROM PRODUCT", out)
            self.assertIn("environment", out)
            self.assertTrue(report(tmp)["gaps"]["proof_not_from_product"])

    def test_a_wrong_state_outside_the_path_is_not_a_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "check_calc.py", "import os, sys\nsys.exit(0 if not os.path.exists('off.flag') "
                                        "else (print('expected total 42') or 1))\n")
            write(tmp, "VERIFY.md", recipe().replace("python -m unittest test_calc.py",
                                                     "python check_calc.py && python -m unittest test_calc.py"))
            write(tmp, "off.flag")
            run("verify.py", "run", tmp)
            os.remove(os.path.join(tmp, "off.flag"))
            run("verify.py", "baseline", tmp)
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("PROOF NOT FROM PRODUCT  when it went red, the files differed from today's in off.flag", out)

    def test_an_unrestored_red_is_still_reported_as_a_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "calc.py", BAD)
            run("verify.py", "run", tmp)
            a = report(tmp)
            self.assertEqual([r["feature"] for r in a["rejections"]], ["Total"])

    def test_receipts_share_one_tree_per_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp, extra="\n## Total again\n- path: calc.py\n- test: `python -m unittest test_calc.py -q`\n"
                               "- fail-signal: expected total 42\n- fail-proof: total adds one\n")
            prove(tmp)
            with open(os.path.join(tmp, ".verify-state.json"), encoding="utf-8") as fh:
                state = json.load(fh)
            receipts = state["failures"].values()
            self.assertEqual(len(receipts), 2)
            self.assertTrue(all("files" not in r for r in receipts))
            self.assertEqual(len({r["files_id"] for r in receipts}), 1)
            self.assertEqual(list(state["receipt_trees"]), [next(iter(receipts))["files_id"]])
            self.assertEqual(report(tmp)["verdict"], "green")


class Loosened(unittest.TestCase):
    def history(self, tmp, loosened):
        project(tmp)
        git(tmp, "init", "-q")
        write(tmp, ".gitignore", ".verify-state*\n__pycache__/\n")
        git(tmp, "add", "-A")
        git(tmp, "commit", "-qm", "total with an exact check")
        write(tmp, "test_calc.py", TEST.replace(loosened[0], loosened[1]))
        git(tmp, "commit", "-qam", "test: deflake total")

    def test_equality_made_tolerant_keeps_strict_red_and_names_the_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.history(tmp, ("self.assertEqual(total(40, 2), 42,", "self.assertAlmostEqual(total(40, 2), 42, delta=2, msg="))
            write(tmp, "calc.py", BAD)
            run("verify.py", "run", tmp)
            write(tmp, "calc.py", GOOD)
            code, out, _ = run("verify.py", "baseline", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("BASELINE REFUSED  loosened: test_calc.py::T.test_total", out)
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("LOOSENED  test_calc.py::T.test_total: 1 -> 0 exact assertions", out)
            self.assertIn("test: deflake total", out)

    def test_a_changed_expected_value_is_loosened_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.history(tmp, ("total(40, 2), 42,", "total(40, 2), 43,"))
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("expected values changed", out)

    def test_a_reworded_message_is_not_loosened(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.history(tmp, ("'expected total 42'", "'expected the total 42'"))
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertNotIn("LOOSENED", out)

    def test_a_review_before_the_commit_still_holds_after_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            git(tmp, "init", "-q")
            write(tmp, ".gitignore", ".verify-state*\n__pycache__/\n")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-qm", "exact")
            write(tmp, "test_calc.py", TEST.replace("self.assertEqual(total(40, 2), 42,",
                                                    "self.assertAlmostEqual(total(40, 2), 42, delta=2, msg="))
            code, out, _ = run("verify.py", "baseline", tmp, "--reviewed-by", "maya", "--reason", "spec allows 2")
            self.assertEqual(code, 0, out)
            git(tmp, "commit", "-qam", "tolerance per spec")
            code, out, _ = run("verify.py", "baseline", tmp)
            self.assertEqual(code, 0, out)
            self.assertNotIn("LOOSENED", run("verify.py", "run", tmp, "--strict")[1])

    def test_a_person_reviewing_it_clears_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.history(tmp, ("self.assertEqual(total(40, 2), 42,", "self.assertAlmostEqual(total(40, 2), 42, delta=2, msg="))
            write(tmp, "calc.py", "def total(a, b):\n    return a + b + 5\n")
            run("verify.py", "run", tmp)
            write(tmp, "calc.py", GOOD)
            code, out, _ = run("verify.py", "baseline", tmp, "--reviewed-by", "maya", "--reason", "spec allows 2")
            self.assertEqual(code, 0, out)
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertEqual(code, 0, out)
            self.assertNotIn("LOOSENED", out)

    def test_an_uncommitted_loosening_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            git(tmp, "init", "-q")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-qm", "exact")
            write(tmp, "test_calc.py", TEST.replace("self.assertEqual(total(40, 2), 42,",
                                                    "self.assertTrue(total(40, 2),"))
            code, out, _ = run("verify.py", "run", tmp, "--strict")
            self.assertIn("LOOSENED  test_calc.py::T.test_total", out)
            self.assertIn("working tree", out)


class Blocked(unittest.TestCase):
    def test_a_missing_tool_is_blocked_not_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "VERIFY.md", recipe().replace("python -m unittest test_calc.py",
                                                     "python -c \"import nosuchmodule_xyz\""))
            code, out, _ = run("verify.py", "run", tmp)
            self.assertIn("BLOCKED", out)
            a = report(tmp)
            self.assertEqual(len(a["gaps"]["blocked"]), 1)
            self.assertEqual([t["action"] for t in a["next"]], ["blocked"])
            self.assertIn("do not change product code", a["next"][0]["next"])
            text = run("verify.py", "report", tmp)[1]
            self.assertIn("GAP  blocked by the environment: Total|", text)

    def test_a_missing_python_suggests_python3(self):
        import sys
        from unittest import mock
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugin", "skills", "verify-loop", "scripts"))
        import verify
        for out in ("/bin/sh: python: command not found", "zsh: command not found: python",
                    "/bin/sh: 1: python: not found", "bash: line 1: python: command not found",
                    "xcode-select: Failed to locate 'python', requesting installation of command line developer tools.",
                    "'python' is not recognized as an internal or external command"):
            with mock.patch.object(verify.shutil, "which", return_value="/usr/bin/python3"):
                category, summary, _ = verify.diagnose_failure(out, 127, "")
            self.assertEqual(category, "harness-gap", out)
            self.assertIn("`python3` is", summary, out)
            with mock.patch.object(verify.shutil, "which", return_value=None):
                category, summary, _ = verify.diagnose_failure(out, 127, "")
            self.assertEqual(category, "harness-gap", out)
            self.assertNotIn("python3", summary, out)
        for out in ("sh: python3: command not found", "AssertionError: python: not found in list"):
            with mock.patch.object(verify.shutil, "which", return_value="/usr/bin/python3"):
                self.assertNotIn("`python3` is", verify.diagnose_failure(out, 1, "")[1], out)

    def test_the_macos_python_stub_is_blocked_not_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "stub.py", "import sys\nsys.stderr.write(\"xcode-select: Failed to locate 'python', "
                                  "requesting installation of command line developer tools.\\n\")\nsys.exit(72)\n")
            write(tmp, "VERIFY.md", recipe().replace("python -m unittest test_calc.py", "python stub.py"))
            out = run("verify.py", "run", tmp)[1]
            self.assertIn("BLOCKED", out)
            self.assertEqual([t["action"] for t in report(tmp)["next"]], ["blocked"])


if __name__ == "__main__":
    unittest.main()
