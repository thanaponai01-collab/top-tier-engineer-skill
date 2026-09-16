#!/usr/bin/env python3
"""
The eval suite, held by a test.

Two things have to stay true, and the second is the one that matters:

  1. Every case is well formed — a prompt, a fixture, expectations, and the two
     reference reports.
  2. The grader discriminates. Each case ships a report that must pass and a
     report that must fail. A grader that passes everything would sit here
     green forever while telling you nothing, so it is checked against both.

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
            for part in ("prompt.md", "fixture", "reference/good.md", "reference/bad.md"):
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


if __name__ == "__main__":
    unittest.main()
