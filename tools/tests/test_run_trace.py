#!/usr/bin/env python3
"""run-trace.py — did the run actually execute the stages it should have."""
import json, unittest
from _helpers import run


class RunTrace(unittest.TestCase):
    def _json(self, stdin):
        code, out, err = run("run-trace.py", "--json", stdin=stdin)
        self.assertNotIn("Traceback", err)
        return code, json.loads(out)

    def test_complete_build_passes(self):
        code, r = self._json("SUBJECT: demo @ abc1234\nSLICE: proven(x)\nGATE: pass(x)\n")
        self.assertEqual(code, 0)
        self.assertEqual(r["request_type"], "build")
        self.assertEqual(r["missing_required"], [])

    def test_build_missing_gate_is_incomplete_not_misclassified(self):
        # Regression guard: a SLICE-only build must stay classified as "build" and
        # demand GATE — not be mislabeled as a "fix" (which would demand CAUSE/MAINT).
        code, r = self._json("SLICE: proven(x)\n")
        self.assertEqual(code, 1)
        self.assertEqual(r["request_type"], "build")
        self.assertIn("GATE", r["missing_required"])

    def test_fix_run_classifies_as_fix(self):
        code, r = self._json("SUBJECT: demo @ unversioned(pasted snippet)\n"
                             "CAUSE: proven(root cause)\nMAINT: resolved(patched)\n")
        self.assertEqual(code, 0)
        self.assertEqual(r["request_type"], "fix")

    def test_no_verdicts_is_no_trace(self):
        code, r = self._json("hello world, nothing structured here\n")
        self.assertEqual(code, 2)

    def test_classified_run_without_subject_pin_is_incomplete(self):
        # PROTOCOL §1 pin rule (AUDIT_001): a classified run whose report never records the
        # revision it read is incomplete — its file:line quotes are floating evidence.
        code, r = self._json("REVIEW: shippable-with-findings(top: x)\n")
        self.assertEqual(code, 1)
        self.assertIn("SUBJECT", r["missing_required"])

    def test_subject_pin_satisfies_pin_rule(self):
        code, r = self._json("SUBJECT: tickit @ 9f3ab21 +dirty\n"
                             "REVIEW: shippable-with-findings(top: x)\n")
        self.assertEqual(code, 0)
        self.assertNotIn("SUBJECT", r["missing_required"])


if __name__ == "__main__":
    unittest.main()
