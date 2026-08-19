#!/usr/bin/env python3
"""
verdict-lint.py — PROTOCOL §5 verdict-line form, §11 DELIVERY block, release drift.

Part of the suite's own test floor; run them all with `python3 tools/test_tools.py`.
"""
import json, os, tempfile, unittest

from _helpers import run


# PROTOCOL §11: the four lines every director-facing report opens with. Kept here as one
# constant so the multi-noun fixtures below read as reports, not as verdict soup.
DELIVERY = ('ASKED: "make the login stop dropping people on refresh"\n'
            "DID: sessions now survive a page reload.\n"
            "SO: you stay logged in when you refresh; nothing else changed.\n"
            "COST: one new file you now own; no new steps to run.\n")

class VerdictLint(unittest.TestCase):
    def test_clean_transcript_passes(self):
        code, out, _ = run("verdict-lint.py",
                            stdin=DELIVERY + "SLICE: proven(x wired)\nGATE: pass(x)\n")
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

    # ---- BACKLOG (v1.22.0, DECISION_LEDGER D006) ----

    def test_backlog_legal_states_pass(self):
        code, out, _ = run("verdict-lint.py",
                            stdin="BACKLOG: filed(7, top: N+1 on the roster read)\n")
        self.assertEqual(code, 0, out)

    def test_backlog_illegal_state_fails(self):
        code, out, _ = run("verdict-lint.py", stdin="BACKLOG: done(all of it)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("BACKLOG", out)

    # ---- PROTOCOL §9 delivered-fix discipline (AUDIT_001) ----

    def test_fix_coherent_without_scrutiny_fails(self):
        # The exact LIVE_RUN_004 failure: a delivered fix adjudicated by nobody.
        code, out, _ = run("verdict-lint.py",
                            stdin="FIX F1: coherent(surfaces: api, ui)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("SCRUTINY", out)

    def test_fix_coherent_with_scrutiny_passes(self):
        code, out, _ = run("verdict-lint.py",
                            stdin=DELIVERY + "SCRUTINY: fix-then-ship(top: parity)\n"
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

    # ---- PROTOCOL §11 the sense floor (director report: does it answer the ask?) ----

    def test_multi_stage_report_without_delivery_block_fails(self):
        # The gap this rule closes: every gate green, and no line in the report is
        # checkable against the sentence the director actually wrote.
        code, out, _ = run("verdict-lint.py",
                            stdin="SLICE: proven(x)\nGATE: pass(x)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("ASKED", out)

    def test_lifecycle_line_alone_requires_delivery_block(self):
        # One noun, but LIFECYCLE means chief-engineer is reporting to the director.
        code, out, _ = run("verdict-lint.py",
                            stdin="LIFECYCLE: building | next: correctness-gate\n")
        self.assertEqual(code, 1, out)
        self.assertIn("§11", out)

    def test_isolated_gate_agent_is_exempt(self):
        # A §8.2 subagent reports to the merging skill, not the director. Requiring a
        # DELIVERY block here would wedge exactly the parallel gates §8.2 enables.
        code, out, _ = run("verdict-lint.py", stdin="GATE: fail(login accepts empty pw)\n")
        self.assertEqual(code, 0, out)

    def test_asked_must_quote_the_director(self):
        # The paraphrase IS the drift — a summarized ASKED cannot be checked by a reader
        # who was not present, which is the whole point of quoting it.
        paraphrased = DELIVERY.replace(
            'ASKED: "make the login stop dropping people on refresh"',
            "ASKED: user wanted better session handling")
        code, out, _ = run("verdict-lint.py",
                            stdin=paraphrased + "SLICE: proven(x)\nGATE: pass(x)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("quote", out)

    def test_partial_delivery_block_names_the_missing_field(self):
        partial = DELIVERY.replace("COST: one new file you now own; no new steps to run.\n", "")
        code, out, _ = run("verdict-lint.py",
                            stdin=partial + "SLICE: proven(x)\nGATE: pass(x)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("COST", out)

    def test_bold_markdown_delivery_block_is_recognized(self):
        # Reports are markdown; the fields will be bolded in real use.
        bolded = "".join(f"- **{l}\n" for l in DELIVERY.strip().splitlines())
        code, out, _ = run("verdict-lint.py",
                            stdin=bolded + "\nSLICE: proven(x)\nGATE: pass(x)\n")
        self.assertEqual(code, 0, out)

    def test_pre_sense_floor_vintage_is_grandfathered(self):
        # A rule may not condemn an artifact written before it existed (PROTOCOL §11,
        # rule vintage). The legacy run transcripts in runs/ depend on this.
        code, out, _ = run("verdict-lint.py",
                            stdin="PROTOCOL: 1.12.0 — predates the sense floor\n"
                                  "SLICE: proven(x)\nGATE: pass(x)\n")
        self.assertEqual(code, 0, out)

    def test_current_vintage_is_not_grandfathered(self):
        # The escape hatch must not become a way to opt out of today's rules.
        code, out, _ = run("verdict-lint.py",
                            stdin="PROTOCOL: 1.16.0\nSLICE: proven(x)\nGATE: pass(x)\n")
        self.assertEqual(code, 1, out)
        self.assertIn("ASKED", out)

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

    def _release_with_marketplace(self, entries):
        """Build an agreeing plugin.json/CHANGELOG repo, optionally add a marketplace
        listing `entries` (None = no marketplace file at all), and run --release."""
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, "1.2.0", "1.2.0")
            if entries is not None:
                with open(os.path.join(tmp, ".claude-plugin", "marketplace.json"), "w",
                          encoding="utf-8") as f:
                    json.dump({"name": "m", "plugins": entries}, f)
            return run("verdict-lint.py", "--release", tmp)

    def test_marketplace_drift_fails(self):
        """v1.16.0 bumped plugin.json and CHANGELOG and left marketplace.json behind,
        and the gate said 'release clean' — it only knew about two of the three
        surfaces that state a version."""
        code, out, _ = self._release_with_marketplace([{"name": "x", "version": "1.1.0"}])
        self.assertEqual(code, 1, out)
        self.assertIn("marketplace.json", out)

    def test_marketplace_agreeing_is_clean(self):
        code, out, _ = self._release_with_marketplace([{"name": "x", "version": "1.2.0"}])
        self.assertEqual(code, 0, out)

    def test_marketplace_matches_on_name_not_position(self):
        """A marketplace may list several plugins; only THIS one's entry binds."""
        code, out, _ = self._release_with_marketplace(
            [{"name": "other", "version": "9.9.9"}, {"name": "x", "version": "1.2.0"}])
        self.assertEqual(code, 0, out)

    def test_absent_marketplace_is_not_a_failure(self):
        """Publishing a marketplace is optional; its absence must not fail a repo."""
        code, out, _ = self._release_with_marketplace(None)
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
