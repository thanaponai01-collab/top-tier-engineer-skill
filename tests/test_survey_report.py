"""1.22.0: `report` shows the last `challenge --auto` score for the current checks and tree, so a 10/10
survey no longer reads as "nothing here is proven able to fail". It is still a lead, not a receipt.

Run with: python -m unittest discover tests
"""
import json, tempfile, unittest
from pathlib import Path

from _helpers import run

APP = "def grade(score):\n    if score >= 50:\n        return 'pass'\n    return 'fail'\n"
TEST = "from app import grade\nassert grade(50) == 'pass', 'expected pass'\nassert grade(49) == 'fail', 'expected fail'\n"


def project(root):
    Path(root, "app.py").write_text(APP, encoding="utf-8")
    Path(root, "test_grade.py").write_text(TEST, encoding="utf-8")
    Path(root, "VERIFY.md").write_text("## Grade\n- path: app.py\n- test: `python test_grade.py`\n"
                                       "- fail-signal: expected\n", encoding="utf-8")


class SurveyInReport(unittest.TestCase):
    def test_report_shows_the_survey_score(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            run("verify.py", "run", root)
            code, out, err = run("verify.py", "challenge", root, "--feature", "Grade", "--auto")
            self.assertEqual(code, 0, out + err)
            _, out, _ = run("verify.py", "report", root)
            self.assertIn("SURVEY  Grade:", out)
            self.assertIn("caught (100%)", out)
            self.assertIn("not a receipt", out)
            self.assertIn("GAP  never seen red: Grade", out)  # still not a proof
            _, out, _ = run("verify.py", "report", root, "--json")
            survey = json.loads(out)["surveys"]["Grade"]
            self.assertEqual(survey["score"], 1.0)

    def test_survey_is_shown_with_assess_and_no_run(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as state:
            project(root)
            run("verify.py", "challenge", root, "--feature", "Grade", "--auto", "--state-dir", state)
            _, out, _ = run("verify.py", "report", root, "--state-dir", state)
            self.assertIn("SURVEY  Grade:", out)
            self.assertNotIn("nothing here is proven able to fail", out)

    def test_a_product_edit_makes_the_survey_stale(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            run("verify.py", "challenge", root, "--feature", "Grade", "--auto")
            Path(root, "app.py").write_text(APP.replace(">= 50", ">= 60"), encoding="utf-8")
            _, out, _ = run("verify.py", "report", root)
            self.assertNotIn("SURVEY  Grade:", out)

    def test_survey_records_no_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            run("verify.py", "challenge", root, "--feature", "Grade", "--auto")
            self.assertFalse(Path(root, ".verify-state.json").exists())


if __name__ == "__main__":
    unittest.main()
