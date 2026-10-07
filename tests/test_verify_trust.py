import sys
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
from verify_trust import summarize
import grade


class TrustScorecard(unittest.TestCase):
    def setUp(self):
        self.policy = {"skill": "verify-loop", "minimum_repeats": 2,
                       "minimum_task_pass_rate": 0.95, "maximum_guardrail_failure_rate": 0,
                       "development": ["broken"], "held_out": ["healthy"],
                       "guardrail_cases": ["broken", "healthy"]}
        self.rows = [{"skill": "verify-loop", "case": c, "arm": "with",
                      "passed": True, "tripped": []} for c in ("broken", "healthy") for _ in range(2)]

    def test_complete_success_meets_bar(self):
        self.assertTrue(summarize(self.rows, self.policy)["bar_met"])

    def test_missing_case_cannot_be_averaged_away(self):
        self.assertFalse(summarize(self.rows[:2], self.policy)["bar_met"])

    def test_trap_failure_blocks_despite_pass_field(self):
        self.rows[0]["tripped"] = ["incorrect approval"]
        self.assertFalse(summarize(self.rows, self.policy)["bar_met"])

    def test_errors_do_not_count_as_successful_repeats(self):
        self.rows[0]["errored"] = True
        result = summarize(self.rows, self.policy)
        self.assertFalse(result["bar_met"])
        self.assertEqual(result["splits"]["development"]["invalid_runs"], 1)

    def test_missing_trap_data_is_unknown(self):
        del self.rows[0]["tripped"]
        self.assertFalse(summarize(self.rows, self.policy)["bar_met"])

    def test_without_arm_cannot_fill_with_coverage(self):
        self.rows[0]["arm"] = "without"
        self.assertFalse(summarize(self.rows, self.policy)["bar_met"])


class HealthyFixture(unittest.TestCase):
    def test_check_accepts_spec_and_rejects_wrong_boundary(self):
        case = grade.load_case("verify-loop-healthy-check")
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(Path(case["dir"]) / "fixture", tmp, dirs_exist_ok=True)
            command = [sys.executable, "-B", "-m", "unittest", "test_shipping"]
            good = subprocess.run(command, cwd=tmp, capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            source = Path(tmp) / "shipping.py"
            source.write_text(source.read_text().replace("total < 50", "total <= 50"))
            bad = subprocess.run(command, cwd=tmp, capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("AssertionError", bad.stderr)

    def test_reference_grades_accept_good_and_reject_bad(self):
        case = grade.load_case("verify-loop-healthy-check")
        ref = Path(case["dir"]) / "reference"
        self.assertTrue(grade.grade(case, (ref / "good.md").read_text())["passed"])
        self.assertFalse(grade.grade(case, (ref / "bad.md").read_text())["passed"])
