#!/usr/bin/env python3
"""verdict-lint.py — verdict-line form and the §9 delivered-fix discipline."""
import json, os, tempfile, unittest
from _helpers import run


class VerdictLint(unittest.TestCase):
    def test_clean_transcript_passes(self):
        code, out, _ = run("verdict-lint.py",
                            stdin="SLICE: proven(x wired)\nGATE: pass(x)\n")
        self.assertEqual(code, 0, out)
        self.assertIn("clean", out)

    def test_bad_state_reports_correct_line(self):
        # Regression: the off-by-one that reported the wrong line number. The bad
        # verdict is on line 3; the message must say "line 3", not 2 or 4.
        code, out, _ = run("verdict-lint.py", stdin="one\ntwo\nGATE: banana(x)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("line 3", out)

    def test_trace_only_without_bold_marker_fails(self):
        code, out, _ = run("verdict-lint.py",
                            stdin="prose line\nSLICE: trace-only(not executed)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("trace-only", out)

    def test_out_of_order_ship_fails(self):
        # SHIP: go with no preceding GATE: pass violates the §4 handoff chain.
        code, out, _ = run("verdict-lint.py", stdin="SHIP: go(canary, tag v1)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("GATE: pass", out)

    def test_no_verdicts_is_soft_pass(self):
        code, out, _ = run("verdict-lint.py", stdin="just some prose, no verdicts\n")
        self.assertEqual(code, 0, out)

    # ---- PROTOCOL §9 delivered-fix discipline (AUDIT_001) ----

    def test_fix_coherent_without_scrutiny_fails(self):
        # The exact LIVE_RUN_004 failure: a delivered fix adjudicated by nobody.
        code, out, _ = run("verdict-lint.py",
                            stdin="FIX F1: coherent(surfaces: api, ui)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("SCRUTINY", out)

    def test_fix_coherent_with_scrutiny_passes(self):
        code, out, _ = run("verdict-lint.py",
                            stdin="SCRUTINY: fix-then-ship(top: parity)\n"
                                  "FIX F1: coherent(surfaces: api, ui, export)\n")
        self.assertEqual(code, 0, out)

    def test_fix_unscrutinized_needs_bold_marker(self):
        code, out, _ = run("verdict-lint.py", stdin="FIX F1: unscrutinized\n")
        self.assertEqual(code, 1, out)
        self.assertIn("unscrutinized", out)

    def test_fix_unscrutinized_with_marker_passes(self):
        code, out, _ = run("verdict-lint.py",
                            stdin="**Limitation: no outsider pass ran on this fix.**\n"
                                  "FIX F1: unscrutinized\n")
        self.assertEqual(code, 0, out)

    def test_fix_bad_state_fails(self):
        code, out, _ = run("verdict-lint.py", stdin="FIX F1: shipped(done)\n")
        self.assertEqual(code, 1, out)

    def test_fix_prose_with_parenthetical_is_not_a_verdict(self):
        # Regression (LIVE_RUN_002 line 75): §9 grammar is `FIX <id>:` with a bare-token id;
        # prose like this must not be linted as a malformed FIX verdict.
        code, out, _ = run("verdict-lint.py",
                            stdin="FIX (single batched IN-clause): 1 DB round trip\n")
        self.assertEqual(code, 0, out)


class VerdictLintRelease(unittest.TestCase):
    def _repo(self, tmp, plugin_ver, changelog_ver):
        os.makedirs(os.path.join(tmp, ".claude-plugin"))
        with open(os.path.join(tmp, ".claude-plugin", "plugin.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"name": "x", "version": plugin_ver}, f)
        with open(os.path.join(tmp, "CHANGELOG.md"), "w", encoding="utf-8") as f:
            f.write(f"## {changelog_ver} - today\n")

    def test_matching_versions_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, "1.2.0", "1.2.0")
            code, out, _ = run("verdict-lint.py", "--release", tmp)
            self.assertEqual(code, 0, out)

    def test_version_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, "1.2.0", "1.1.0")
            code, out, _ = run("verdict-lint.py", "--release", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("drift", out)


if __name__ == "__main__":
    unittest.main()
