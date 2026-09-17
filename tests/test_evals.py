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
import os, sys, unittest

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
