"""The change-verification grader must reject missing adjacent regression coverage."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from _helpers import ROOT, run

sys.path.insert(0, os.path.join(ROOT, "evals"))
import grade


class ChangeEvaluation(unittest.TestCase):
    def setUp(self):
        self.case = grade.load_case("verify-loop-change-shared-caller")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name, "work")
        shutil.copytree(Path(self.case["dir"], "fixture"), self.work)
        shutil.copytree(Path(self.case["dir"], "reference", "solution"), self.work, dirs_exist_ok=True)
        for feature in ("Shipping", "Discount"):
            code, out, err = run("verify.py", "challenge", str(self.work), "--feature", feature,
                                 "--mutation", str(self.work / f"mutation_{feature.lower()}.json"))
            self.assertEqual(code, 0, out + err)
        self.assertEqual(run("verify.py", "baseline", str(self.work))[0], 0)
        code, out, err = run("verify.py", "run", str(self.work), "--strict")
        self.assertEqual(code, 0, out + err)
        self.good = Path(self.case["dir"], "reference", "good.md").read_text()

    def result(self):
        return grade.grade(self.case, self.good, str(self.work))

    def failed_checks(self, result):
        return {c["id"] for c in result["workdir"]["checks"] if not c["ok"]}

    def test_executed_reference_solution_passes(self):
        result = self.result()
        self.assertTrue(result["passed"], grade.render(result))
        state = json.loads((self.work / ".verify-state.json").read_text())
        self.assertEqual(len(state["failures"]), 2)

    def test_passing_changed_behavior_cannot_hide_weak_adjacent_check(self):
        shutil.copyfile(Path(self.case["dir"], "fixture", "test_discount.py"), self.work / "test_discount.py")
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertIn("detects-shared-regression", self.failed_checks(result))

    def test_correct_product_without_strict_evidence_is_incomplete(self):
        (self.work / ".verify-state.json").unlink()
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertIn("strict-current-green", self.failed_checks(result))

    def test_original_regression_cannot_pass_on_report_alone(self):
        shutil.copyfile(Path(self.case["dir"], "fixture", "commerce.py"), self.work / "commerce.py")
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertIn("finished-product-meets-spec", self.failed_checks(result))

    def test_removing_adjacent_feature_is_not_completion(self):
        path = self.work / "VERIFY.md"
        path.write_text(path.read_text().split("## Discount")[0])
        result = self.result()
        self.assertFalse(result["passed"])
        self.assertIn("scope-adjacent-claim", self.failed_checks(result))
