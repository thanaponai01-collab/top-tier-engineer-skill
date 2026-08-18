#!/usr/bin/env python3
"""
run-trace.py — run-completeness classification over a transcript.

Part of the suite's own test floor; run them all with `python3 tools/test_tools.py`.
"""
import json, re, unittest

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

    def test_pre_pin_rule_vintage_is_grandfathered(self):
        """PROTOCOL §11 rule vintage, which is stated as GENERAL: "every check added after
        this one inherits the mechanism". The pin rule arrived in 1.13.0, so a transcript
        declaring 1.12.0 may not be condemned by it. This test exists because that
        inheritance was prose only — verdict-lint implemented the mechanism privately and
        run-trace had no notion of it, so three transcripts that correctly declared their
        vintage were failed by a check younger than they were."""
        code, r = self._json("PROTOCOL: 1.12.0\n"
                             "REVIEW: shippable-with-findings(top: x)\n")
        self.assertEqual(code, 0, r)
        self.assertNotIn("SUBJECT", r["missing_required"])

    def test_current_vintage_still_owes_a_subject_pin(self):
        """The other half: grandfathering must not become a way to opt out. A transcript
        declaring a vintage at or after the check still answers to it."""
        code, r = self._json("PROTOCOL: 1.16.0\n"
                             "REVIEW: shippable-with-findings(top: x)\n")
        self.assertEqual(code, 1)
        self.assertIn("SUBJECT", r["missing_required"])

    def test_undeclared_vintage_is_judged_by_current_rules(self):
        """§11: "a transcript with no declaration is judged by the current rules" — so
        simply omitting the line can never silence a check."""
        code, r = self._json("REVIEW: shippable-with-findings(top: x)\n")
        self.assertEqual(code, 1)
        self.assertIn("SUBJECT", r["missing_required"])

    def test_latent_sweep_is_traceable(self):
        """LATENT is a §5 registry noun (latent-audit, 1.14.0) that run-trace did not
        recognise at all, so no latent-audit run could ever be checked for completeness —
        its verdict was silently discarded as an unknown noun."""
        code, r = self._json("SUBJECT: repo @ abc1234\n"
                             "LATENT: findings(dead: 0, unused: 0, layer-breaches: 0)\n")
        self.assertEqual(code, 0, r)
        self.assertEqual(r["request_type"], "latent")


if __name__ == "__main__":
    unittest.main()
