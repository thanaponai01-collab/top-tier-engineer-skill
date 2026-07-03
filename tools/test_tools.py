#!/usr/bin/env python3
"""
test_tools — the suite's tools gate their own correctness.

correctness-gate is a skill that demands proof over plausibility; the tools that
enforce it (verdict-lint, run-trace, structure-report) shipped with zero tests and
had already regressed twice (a UTF-8 crash, a verdict-line off-by-one, a false-fix
classification). This suite is the smallest thing that fails if any of those return.

Stdlib only — no pytest, no fixtures framework. Run: `python tools/test_tools.py`.
Each tool is exercised through its real CLI (exit codes are its contract), so this
also covers the stdout-encoding path that caused the historical Windows crash.
"""
import subprocess, sys, os, json, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def run(tool, *args, stdin=None):
    """Invoke a tool through its CLI; return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, tool), *args],
        input=stdin, capture_output=True, text=True, encoding="utf-8",
    )
    return p.returncode, p.stdout, p.stderr


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


class StructureReport(unittest.TestCase):
    def _dir(self, name, body):
        tmp = tempfile.mkdtemp()
        with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
            f.write(body)
        return tmp

    def test_clean_file_passes(self):
        tmp = self._dir("ok.py", "def add(a, b):\n    return a + b\n")
        code, out, err = run("structure-report.py", tmp)
        self.assertNotIn("Traceback", err)
        self.assertEqual(code, 0, out)

    def test_non_ascii_source_does_not_crash(self):
        # Regression: a source file with non-ASCII bytes crashed the reporter on
        # Windows (cp1252 stdout). It must scan cleanly and never raise.
        body = "# ผู้ใช้ comment 你好 🚀\ndef f():\n    return 'café'\n"
        tmp = self._dir("uni.py", body)
        code, out, err = run("structure-report.py", tmp)
        self.assertNotIn("Traceback", err)
        self.assertIn(code, (0, 1), err)

    def test_deep_nesting_is_flagged(self):
        # A pathologically nested function must trip a threshold (exit 1, findings).
        lines = ["def deep(x):"]
        indent = "    "
        for i in range(12):
            lines.append(indent * (i + 1) + f"if x > {i}:")
        lines.append(indent * 13 + "return x")
        tmp = self._dir("deep.py", "\n".join(lines) + "\n")
        code, out, err = run("structure-report.py", tmp)
        self.assertNotIn("Traceback", err)
        self.assertEqual(code, 1, out)
        self.assertIn("findings", out)


class GraphAudit(unittest.TestCase):
    """graph-audit.py — planted-defect fixture: one upward import, one dead
    module, one unused def, one entry point that must NOT be flagged, and one
    raw-text rescue (a module referenced only from a yml is not dead)."""

    def _fixture(self, tmp, with_yml_rescue=False):
        def w(rel, text):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(text)
        w("main.py", 'from app.routes.orders import order_page\n'
                     'if __name__ == "__main__":\n    order_page()\n')
        w("app/routes/orders.py", "from app.services.billing import charge\n"
                                  "def order_page():\n    return charge(10)\n")
        w("app/services/billing.py",
          "from app.models.invoice import Invoice\n"
          "from app.routes.orders import order_page\n"   # upward: domain -> interface
          "def charge(amount):\n    return Invoice(amount)\n"
          "def legacy_discount(amount):\n    return amount * 0.9\n")
        w("app/models/invoice.py",
          "class Invoice:\n    def __init__(self, amount):\n"
          "        self.amount = amount\n")
        w("app/services/old_report.py",
          'def build_report():\n    return "report"\n')
        w("layers.txt", "interface: app/routes/\ndomain: app/services/\n"
                        "data: app/models/\n")
        if with_yml_rescue:
            w("tasks.yml", "report_task: app.services.old_report\n")
        return os.path.join(tmp, "layers.txt")

    def test_planted_defects_all_caught_entry_spared(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp)
            code, out, err = run("graph-audit.py", tmp, "--layers", layers,
                                 "--json")
            self.assertEqual(code, 1, out + err)
            r = json.loads(out)
            self.assertEqual([d["module"] for d in r["dead_modules"]],
                             ["app.services.old_report"])   # main NOT flagged
            self.assertEqual(len(r["layer_breaches"]), 1, r["layer_breaches"])
            self.assertIn("domain", r["layer_breaches"][0]["edge"])
            names = {u["name"] for u in r["unused_defs"]}
            self.assertIn("legacy_discount", names)

    def test_raw_text_reference_rescues_dead_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp, with_yml_rescue=True)
            code, out, err = run("graph-audit.py", tmp, "--layers", layers,
                                 "--json")
            r = json.loads(out)
            self.assertEqual(r["dead_modules"], [], out)

    def test_verdict_line_grammar(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp)
            code, out, _ = run("graph-audit.py", tmp, "--layers", layers)
            last = [l for l in out.splitlines() if l.startswith("LATENT:")][-1]
            self.assertIn("findings(dead: 1, unused:", last)
            # the emitted line must satisfy the suite's own linter
            lcode, lout, _ = run("verdict-lint.py", stdin=last + "\n")
            self.assertEqual(lcode, 0, lout)

    def test_empty_tree_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("graph-audit.py", tmp)
            self.assertEqual(code, 2, out)
            self.assertIn("blocked(no analyzable source)", out)


if __name__ == "__main__":
    unittest.main()
