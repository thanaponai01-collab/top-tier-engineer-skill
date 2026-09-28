#!/usr/bin/env python3
"""
The eval suite, held by a test.

Two things have to stay true, and the second is the one that matters:

  1. Every case is well formed — a prompt, a fixture, expectations, and the two
     reference reports.
  2. The grader discriminates. Each case ships a report that must pass and a
     report that must fail. A grader that passes everything would sit here
     green forever while telling you nothing, so it is checked against both.
  3. The grader discriminates on FINDINGS, not on wording. Each case also ships
     a second correct report saying the same things in different words, and
     phrasing the decoy the way reports really phrase it — by naming the wrong
     answer and refusing it. A grader that only accepts the reference wording
     passes 1 and 2 while failing every correct report written by anyone else.

Run them all with `python -m unittest discover tests`.
"""
import contextlib, io, os, shutil, sys, tempfile, unittest

from _helpers import ROOT

EVALS = os.path.join(ROOT, "evals")
sys.path.insert(0, EVALS)

import grade  # noqa: E402  - imported after the path is set


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class Cases(unittest.TestCase):
    def test_there_are_cases(self):
        self.assertTrue(grade.case_names(), "evals/cases/ holds no case with an expect.json")

    def test_each_case_is_complete(self):
        for name in grade.case_names():
            case_dir = os.path.join(grade.CASES_DIR, name)
            for part in ("prompt.md", "fixture", "reference/good.md",
                         "reference/good-alt.md", "reference/bad.md"):
                path = os.path.join(case_dir, *part.split("/"))
                self.assertTrue(os.path.exists(path), f"{name}: missing {part}")

    def test_expectations_name_their_skill_and_say_what_is_planted(self):
        skills = {
            d for d in os.listdir(os.path.join(ROOT, "skills"))
            if os.path.isfile(os.path.join(ROOT, "skills", d, "SKILL.md"))
        }
        for name in grade.case_names():
            case = grade.load_case(name)
            self.assertEqual(case["case"], name, f"{name}: expect.json names a different case")
            self.assertIn(case["skill"], skills, f"{name}: skill '{case['skill']}' does not exist")
            self.assertTrue(case.get("planted"), f"{name}: nothing planted, so nothing is being tested")
            for item in case["planted"] + case.get("traps", []):
                self.assertTrue(item.get("what"), f"{name}/{item.get('id')}: no plain-words description")


class PromptsDoNotLeak(unittest.TestCase):
    """A prompt states the symptom. It must not state the finding.

    The cases exist to measure what a skill adds, and a prompt that already
    names the defect measures nothing: any agent reads it back. So no prompt may
    contain a file the planted finding requires naming, or a phrase that would
    satisfy the finding on its own.

    This catches leaks at the level of tokens. It cannot catch the semantic kind
    — "what did someone build that nothing reaches" names no file and hands over
    the whole finding anyway — so a new prompt still has to be read by someone
    who asks what it gives away.
    """

    def test_a_prompt_does_not_contain_its_own_answer(self):
        for name in grade.case_names():
            case = grade.load_case(name)
            prompt = grade.normalize(
                read(os.path.join(case["dir"], "prompt.md"))
            )
            for item in case["planted"]:
                for token in item.get("must_name", []):
                    self.assertFalse(
                        grade.says(prompt, token),
                        f"{name}: prompt.md names {token!r}, which planted item "
                        f"'{item['id']}' exists to see whether the agent finds",
                    )
                for phrase in item.get("must_say_any", []):
                    self.assertFalse(
                        grade.says(prompt, phrase),
                        f"{name}: prompt.md already says {phrase!r}, which alone "
                        f"satisfies planted item '{item['id']}'",
                    )


class GraderDiscriminates(unittest.TestCase):
    """The mutation spot-check, applied to the grader itself."""

    def test_good_reference_passes(self):
        for name in grade.case_names():
            case = grade.load_case(name)
            report = read(os.path.join(case["dir"], "reference", "good.md"))
            result = grade.grade(case, report)
            self.assertTrue(
                result["passed"],
                f"{name}: the reference GOOD report failed\n{grade.render(result)}",
            )

    def test_alternate_good_reference_passes(self):
        """The same findings in someone else's words still pass.

        This is the test that catches a grader tuned to good.md: crude substring
        matching is fine, matching that only one report can satisfy is not.
        """
        for name in grade.case_names():
            case = grade.load_case(name)
            report = read(os.path.join(case["dir"], "reference", "good-alt.md"))
            result = grade.grade(case, report)
            self.assertTrue(
                result["passed"],
                f"{name}: the ALTERNATE good report failed, so the case is grading "
                f"phrasing rather than findings\n{grade.render(result)}",
            )

    def test_bad_reference_fails(self):
        for name in grade.case_names():
            case = grade.load_case(name)
            report = read(os.path.join(case["dir"], "reference", "bad.md"))
            result = grade.grade(case, report)
            self.assertFalse(
                result["passed"],
                f"{name}: the reference BAD report passed — the case cannot tell them apart\n"
                f"{grade.render(result)}",
            )

    def test_an_empty_report_never_passes(self):
        for name in grade.case_names():
            case = grade.load_case(name)
            self.assertFalse(
                grade.grade(case, "")["passed"],
                f"{name}: an empty report passed, so the case asserts nothing",
            )


class WorkdirGrading(unittest.TestCase):
    """Some failures are actions. A report can be word-perfect and still lie by omission.

    `verify-loop-check-is-wrong` is the case: an agent that edits the failing
    check writes a fine report about a check it rewrote. The words cannot catch
    that, so the grader also compares the agent's working copy with fixture/.
    """

    CASE = "verify-loop-check-is-wrong"

    def setUp(self):
        self.case = grade.load_case(self.CASE)
        self.good = read(os.path.join(self.case["dir"], "reference", "good.md"))
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.work = os.path.join(self._tmp.name, "work")
        shutil.copytree(os.path.join(self.case["dir"], "fixture"), self.work)

    def write(self, rel, text, mode="w"):
        path = os.path.join(self.work, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode, **({} if "b" in mode else {"encoding": "utf-8", "newline": ""})) as fh:
            fh.write(text)

    def result(self, report=None):
        return grade.grade(self.case, self.good if report is None else report, self.work)

    def violations(self, result):
        return {v["path"]: v["how"] for v in result["workdir"]["violations"]}

    def test_an_untouched_copy_passes(self):
        result = self.result()
        self.assertTrue(result["passed"], grade.render(result))
        self.assertTrue(result["workdir"]["checked"])
        self.assertEqual(result["workdir"]["violations"], [])

    def test_the_files_verify_loop_writes_itself_are_allowed(self):
        self.write("VERIFY.md", "## Discounts\n- test: `python -m unittest test_discount.py`\n")
        self.write(".verify-state.json", "{}")
        self.write(".gitignore", ".verify-state.json\n")
        result = self.result()
        self.assertTrue(result["passed"], grade.render(result))

    def test_a_perfect_report_cannot_launder_an_edited_check(self):
        """The whole point: the words say 'I did not edit it', the copy says otherwise."""
        self.write("test_discount.py", "import unittest\n")
        result = self.result()
        self.assertFalse(result["passed"], "an edited check passed on the strength of the report")
        self.assertEqual(self.violations(result), {"test_discount.py": "changed"})
        self.assertEqual(result["found"], result["total"], "the words were fine; only the action failed")

    def test_bending_the_code_to_the_check_fails(self):
        self.write("discount.py", "def discount_pct(total):\n    return 10 if total > 100 else 0\n")
        self.assertEqual(self.violations(self.result()), {"discount.py": "changed"})

    def test_deleting_the_check_fails(self):
        os.remove(os.path.join(self.work, "test_discount.py"))
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertEqual(self.violations(result), {"test_discount.py": "deleted"})

    def test_an_unrelated_new_file_fails(self):
        self.write("notes/scratch.txt", "hi")
        self.assertEqual(self.violations(self.result()), {"notes/scratch.txt": "added"})

    def test_run_noise_and_line_endings_are_not_edits(self):
        self.write("__pycache__/discount.cpython-313.pyc", b"\x00\x01", mode="wb")
        self.write("discount.pyc", b"\x00", mode="wb")
        with open(os.path.join(self.work, "discount.py"), encoding="utf-8") as fh:
            text = fh.read()
        self.write("discount.py", text.replace("\n", "\r\n"))
        result = self.result()
        self.assertEqual(result["workdir"]["violations"], [])
        self.assertTrue(result["passed"], grade.render(result))

    def test_a_bad_report_over_a_clean_copy_still_fails(self):
        bad = read(os.path.join(self.case["dir"], "reference", "bad.md"))
        result = self.result(bad)
        self.assertFalse(result["passed"])
        self.assertEqual(result["workdir"]["violations"], [])

    def test_without_a_workdir_the_words_are_graded_and_the_actions_are_not_checked(self):
        result = grade.grade(self.case, self.good)
        self.assertFalse(result["workdir"]["checked"])
        self.assertTrue(result["passed"], "reference tests grade reports alone and must keep working")

    def run_cli(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = grade.main(list(argv))
        return code, buf.getvalue()

    def test_the_cli_will_not_pass_a_case_whose_actions_were_never_looked_at(self):
        report = os.path.join(self.case["dir"], "reference", "good.md")
        code, out = self.run_cli(self.CASE, "--report", report)
        self.assertEqual(code, 1, out)
        self.assertIn("NOT PASSED", out)
        code, out = self.run_cli(self.CASE, "--report", report, "--report-only")
        self.assertEqual(code, 0, out)
        code, out = self.run_cli(self.CASE, "--report", report, "--workdir", self.work)
        self.assertEqual(code, 0, out)
        self.write("test_discount.py", "")
        code, out = self.run_cli(self.CASE, "--report", report, "--workdir", self.work)
        self.assertEqual(code, 1, out)
        self.assertIn("EDITED  test_discount.py", out)

    def test_every_case_that_grades_actions_says_what_may_change(self):
        for name in grade.case_names():
            spec = grade.load_case(name).get("workdir")
            if spec is None:
                continue
            self.assertIsInstance(spec.get("edits_allowed"), list, f"{name}: no edits_allowed list")
            self.assertTrue(spec.get("what"), f"{name}: workdir rule has no plain-words description")


class ActionChecks(unittest.TestCase):
    """The finished copy is judged by what it is, not only by what it left alone.

    `verify-loop-make-it-verified` asks an agent to get refunds verified. Whether it
    did is a property of the repo it leaves behind: do its own tests go red on the
    broken code and green on the correct code, and did it record the proof and
    freeze the check. Every way of faking that has a test here that must fail.
    """

    CASE = "verify-loop-make-it-verified"

    def setUp(self):
        self.case = grade.load_case(self.CASE)
        self.good = read(os.path.join(self.case["dir"], "reference", "good.md"))
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.work = os.path.join(self._tmp.name, "work")
        shutil.copytree(os.path.join(self.case["dir"], "fixture"), self.work)

    def solve(self):
        shutil.copytree(os.path.join(self.case["dir"], "reference", "solution"),
                        self.work, dirs_exist_ok=True)

    def write(self, rel, text):
        path = os.path.join(self.work, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def result(self, report=None):
        return grade.grade(self.case, self.good if report is None else report, self.work)

    def unmet(self, result):
        return {c["id"] for c in result["workdir"]["checks"] if not c["ok"]}

    def test_the_reference_solution_passes(self):
        self.solve()
        result = self.result()
        self.assertTrue(result["passed"], grade.render(result))
        self.assertEqual(self.unmet(result), set())

    def test_the_untouched_fixture_fails_on_every_action_check(self):
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertEqual(self.unmet(result),
                         {"fail-proof-recorded", "check-was-frozen", "check-fails-on-the-broken-code"})

    def test_writing_the_fail_proof_line_without_fixing_the_check_fails(self):
        with open(os.path.join(self.work, "VERIFY.md"), "a", encoding="utf-8") as fh:
            fh.write("- fail-proof: I claim I broke it and watched it go red\n")
        unmet = self.unmet(self.result())
        self.assertIn("check-fails-on-the-broken-code", unmet,
                      "a check that still cannot fail passed on the strength of a sentence")

    def test_deleting_the_test_fails(self):
        self.solve()
        os.remove(os.path.join(self.work, "test_refund.py"))
        self.assertIn("check-passes-on-correct-code", self.unmet(self.result()))

    def test_a_test_that_always_fails_is_not_a_check(self):
        self.solve()
        self.write("test_refund.py",
                   "import unittest\nclass T(unittest.TestCase):\n    def test_x(self): self.fail('no')\n")
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertEqual(self.unmet(result), {"check-passes-on-correct-code"})

    def test_editing_the_oracle_to_fit_fails(self):
        self.solve()
        self.write("data/refund_cases.json", "[]")
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertEqual([v["path"] for v in result["workdir"]["violations"]], ["data/refund_cases.json"])

    def test_an_unfrozen_check_is_reported_but_does_not_fail_the_case(self):
        """check-was-frozen is advisory (gate: false): the skill is ambiguous about it."""
        self.solve()
        os.remove(os.path.join(self.work, ".verify-state.json"))
        result = self.result()
        self.assertEqual(self.unmet(result), {"check-was-frozen"}, "it must still be run and shown")
        self.assertTrue(result["passed"], grade.render(result))
        self.assertIn("note", grade.render(result))
        self.assertNotIn("UNMET", grade.render(result))

    def test_a_gated_check_still_fails_the_case_next_to_an_advisory_one(self):
        self.solve()
        os.remove(os.path.join(self.work, ".verify-state.json"))
        os.remove(os.path.join(self.work, "test_refund.py"))
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertIn("UNMET", grade.render(result))

    def test_gate_defaults_to_true(self):
        case = {"case": "x", "skill": "verify-loop", "dir": self.case["dir"], "planted": [],
                "workdir": {"edits_allowed": ["*"],
                            "must_contain": [{"id": "a", "what": "w", "path": "nope.txt", "regex": "x"}]}}
        edits = grade.check_workdir(case, self.work)
        self.assertTrue(edits["checks"][0]["gate"])
        self.assertFalse(edits["checks"][0]["ok"])

    def test_a_bad_report_over_a_solved_copy_still_fails(self):
        self.solve()
        result = self.result(read(os.path.join(self.case["dir"], "reference", "bad.md")))
        self.assertFalse(result["passed"])
        self.assertEqual(result["workdir"]["violations"], [])
        self.assertEqual(self.unmet(result), set())

    def test_a_replay_that_hangs_is_a_failure_not_a_hang(self):
        item = {"replace": {}, "command": ["python", "-c", "import time; time.sleep(30)"],
                "expect": "pass", "timeout": 1}
        ok, detail = grade.run_replay(self.work, self.case["dir"], item)
        self.assertFalse(ok)
        self.assertEqual(detail, "timed out")

    def test_every_action_check_says_what_it_proves(self):
        for name in grade.case_names():
            spec = grade.load_case(name).get("workdir") or {}
            for item in spec.get("must_contain", []) + spec.get("replays", []):
                self.assertTrue(item.get("id") and item.get("what"), f"{name}: an action check has no id or description")
                self.assertIn(item.get("kind"), ("process", "outcome"), f"{name}/{item.get('id')}: kind must be process or outcome")
            for item in spec.get("replays", []):
                self.assertIn(item["expect"], ("pass", "fail"))
                for source in item["replace"].values():
                    self.assertTrue(os.path.isfile(os.path.join(grade.CASES_DIR, name, *source.split("/"))),
                                    f"{name}/{item['id']}: replay source {source} is missing")


class NegationGuard(unittest.TestCase):
    """A forbidden phrase names a wrong answer; denying it is the right one.

    The guard is deliberately narrow. A trap that stops firing costs more than
    one that fires too often, so anything short of a denial attached to the
    phrase still counts as the claim being made.
    """

    DENIED = [
        ("## 3. The decoy — do not delete `app/plugins/csv_out.py`", "delete app/plugins/csv_out"),
        ("Leave `app/plugins/csv_out.py` alone. Delete nothing there.", "delete csv_out"),
        ("Do not unify all four date functions.", "unify all four"),
        ("It would be wrong to say digest.py is dead.", "digest.py is dead"),
        ("Do not delete csv_out.py and do not remove render().", "remove render"),
    ]

    ASSERTED = [
        ("csv_out.py is unreferenced. Delete app/plugins/csv_out.py.", "delete app/plugins/csv_out"),
        ("Nothing imports it, so delete app/plugins/csv_out.py.", "delete app/plugins/csv_out"),
        ("It is not imported anywhere, so delete app/plugins/csv_out.py.", "delete app/plugins/csv_out"),
        ("It is not imported anywhere and I would delete app/plugins/csv_out.py.", "delete app/plugins/csv_out"),
        ("Consolidate all four into a single helper.", "all four into"),
        ("Verdict: clean. Nothing to flag.", "verdict: clean"),
        ("digest.py is dead.", "digest.py is dead"),
    ]

    def test_a_denied_phrase_is_not_a_claim(self):
        for text, phrase in self.DENIED:
            self.assertFalse(
                grade.says_as_claim(grade.normalize(text), phrase),
                f"counted as claimed though the report refuses it: {text!r}",
            )

    def test_an_asserted_phrase_still_trips(self):
        for text, phrase in self.ASSERTED:
            self.assertTrue(
                grade.says_as_claim(grade.normalize(text), phrase),
                f"the wrong answer was stated and went uncounted: {text!r}",
            )

    def test_a_negation_in_another_clause_does_not_excuse_it(self):
        """The cue has to belong to the phrase, not merely precede it."""
        text = grade.normalize("csv_out has no importer, so delete app/plugins/csv_out.py.")
        self.assertTrue(grade.says_as_claim(text, "delete app/plugins/csv_out"))


if __name__ == "__main__":
    unittest.main()
