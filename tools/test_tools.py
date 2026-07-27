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

    # ---- god-file check must be language-agnostic (regression) ------------------
    def test_long_non_python_file_is_flagged_as_god_file(self):
        """Regression: file-length lived inside the Python-only analyzer, so a
        long .js/.go/.rs file tripped NOTHING while the report claimed other
        languages got 'length + duplication' signals. They got duplication."""
        body = "\n".join(f"var uniqueName{i} = compute{i}({i});" for i in range(900))
        tmp = self._dir("big.js", body + "\n")
        code, out, err = run("structure-report.py", "--json", tmp)
        self.assertNotIn("Traceback", err)
        r = json.loads(out)
        kinds = {f["kind"] for f in r["findings"]}
        self.assertIn("file_lines", kinds, out)
        self.assertEqual(code, 1)

    # ---- opaque code: the reported miss, and its generality ---------------------
    def _hidden(self, body):
        """A Python file whose only mass is `body` held in a value string literal."""
        return "import json\n\nPAGE = \"\"\"" + body + "\"\"\"\n"

    def _opaque_findings(self, source):
        tmp = self._dir("dash.py", source)
        code, out, err = run("structure-report.py", "--json", tmp)
        self.assertNotIn("Traceback", err)
        r = json.loads(out)
        return [f for f in r["findings"] if f["kind"] == "opaque_code"], r

    def test_code_hidden_in_a_string_is_flagged(self):
        """The reported failure: another language's source inside one string literal is
        ONE ast node, so complexity/nesting/function-length all measure zero over it
        and the biggest risk in the file is the part nothing can see."""
        page = ["<!doctype html><html><head><style>"]
        page += [f".panel-{i} {{ color: #0{i % 10}0; }}" for i in range(60)]
        page.append("</style></head><body><script>")
        for i in range(30):
            page += [f"function render{i}(s) {{", f"  if (s.a > {i}) {{",
                     "    return s.b.map(function(x) { return x + 1; });", "  }", "}"]
        page.append("</script></body></html>")
        hits, r = self._opaque_findings(self._hidden("\n".join(page)))
        self.assertEqual(len(hits), 1, r["findings"])
        self.assertGreater(hits[0]["value"], 100, hits)
        self.assertLess(r["coverage"]["pct_entered"], 25, r["coverage"])

    def test_detection_does_not_depend_on_knowing_the_language(self):
        """The generality claim, made falsifiable.

        The first cut of this detector matched `<script`/`function `/`SELECT` — literal
        knowledge of four languages, so the fifth walks past it (Law 6, constrain
        process never intelligence). These two bodies match NO marker anywhere in this
        suite: one is Lua (nests with do/end, ends lines in words, so every C-family
        assumption fails on it) and one is a syntax that does not exist. Both must be
        caught on shape alone. If this test ever needs a vocabulary added to pass, the
        detector has regressed to the version this replaced."""
        lua = []
        for i in range(30):
            lua += [f"local function step{i}(t)", "  for k, v in pairs(t) do",
                    f"    if v > {i} then", "      t[k] = v * 2", "    end", "  end",
                    "  return t", "end"]
        invented = []
        for i in range(40):
            invented += [f"proc handle{i} ~ (state, opts) ->",
                         "    when state?kind == 'lap' ->",
                         "        loop [item <- state?rows] ->",
                         "            yield item?total := item?s1 |+| item?s2",
                         "    otherwise -> nil"]
        for name, body in (("lua", lua), ("invented", invented)):
            hits, r = self._opaque_findings(self._hidden("\n".join(body)))
            self.assertEqual(len(hits), 1, f"{name} not detected: {r['findings']}")

    def test_minified_single_line_bundle_is_flagged(self):
        """A bundle on one 14KB line defeats both tree-signals by construction — it is
        a flattened tree — and is still code nothing can test."""
        blob = "!function(e,t){var n=" + ";".join(f"a{i}=b{i}(c{i})" for i in range(900)) + "}(e,t);"
        hits, r = self._opaque_findings(
            "import json\n\nPAGE = (\n" + "\n".join(f'    "{blob}"' for _ in range(45)) + "\n)\n")
        self.assertEqual(len(hits), 1, r["findings"])

    def test_prose_and_flat_data_are_not_called_code(self):
        """Calibration guard, both directions. A false positive trains the director to
        ignore the alarm, which is worse than silence. Non-English prose is included
        because the obvious shortcut — scoring English function words — would pass the
        English case and silently fail everyone else."""
        cases = {
            "prose-en": "\n".join(
                f"This is paragraph {i} of an ordinary design discussion for humans."
                for i in range(120)),
            "prose-th": "\n".join(
                "นี่คือย่อหน้าที่อธิบายการออกแบบระบบสำหรับผู้อ่านที่เป็นมนุษย์" for _ in range(80)),
            "flat-csv": "\n".join(f"US,United States,{i},840" for i in range(120)),
            "flat-json": "{\n" + "\n".join(f'  "key_{i}": "value_{i}",'
                                           for i in range(120)) + "\n}",
        }
        for name, body in cases.items():
            hits, r = self._opaque_findings(self._hidden(body))
            self.assertEqual(hits, [], f"{name} misclassified as code: {hits}")

    def test_docstrings_are_documentation_not_a_blind_spot(self):
        """Regression: before docstrings were excluded, the suite's own tools produced
        three false positives on their module docstrings — prose in the slot the
        language defines for prose is not an unmeasured region."""
        doc = "\n".join([
            "Usage:", "    tool.py --flag PATH", "        nested example line",
            "", "Explanation of the flag in ordinary prose that runs on for a while.",
        ] * 30)
        tmp = self._dir("doc.py", f'"""\n{doc}\n"""\n\n\ndef f():\n    return 1\n')
        code, out, err = run("structure-report.py", "--json", tmp)
        self.assertNotIn("Traceback", err)
        r = json.loads(out)
        self.assertEqual([f for f in r["findings"] if f["kind"] == "opaque_code"], [], out)
        self.assertGreater(r["coverage"]["documented"], 100, r["coverage"])
        self.assertEqual(r["coverage"]["pct_entered"], 100.0, r["coverage"])

    def test_coverage_is_always_reported(self):
        """PROTOCOL §10 rule 5: a finding count without its denominator lets an
        unmeasured region read as clean. Coverage is not optional output."""
        tmp = self._dir("ok.py", "def add(a, b):\n    return a + b\n")
        code, out, _ = run("structure-report.py", tmp)
        self.assertIn("Coverage:", out)
        self.assertEqual(code, 0, out)


    def test_files_never_opened_are_reported_as_unknown(self):
        """PROTOCOL §10 rule 5 at the SCANNER level, not just the parser level.

        CODE_EXT is a vocabulary, so its omissions are this tool's blind spots. Before
        this, an unadmitted file contributed zero to every signal AND zero to the
        coverage denominator — so the percentage was a fraction of an already-filtered
        population, and 35 unread files rendered as a clean 97.9%."""
        with tempfile.TemporaryDirectory() as tmp:
            for name, body in (("a.py", "def f():\n    return 1\n"),
                               ("README.md", "# docs\n" * 50),
                               ("schema.sql", "SELECT 1;\n" * 50)):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write(body)
            code, out, err = run("structure-report.py", tmp)
            self.assertIn("UNKNOWN", out, out + err)
            self.assertIn("1 of 3 on disk admitted", out)
            self.assertIn("never", out)
            jcode, jout, _ = run("structure-report.py", tmp, "--json")
            cov = json.loads(jout)["coverage"]
            self.assertEqual(cov["files_on_disk"], 3, jout)
            self.assertEqual(cov["files_scanned"], 1)
            self.assertEqual(cov["unscanned"]["files"], 2)

    def test_zero_parser_coverage_never_reads_as_plain_clean(self):
        """The COMMON case, not a corner: any non-Python repo.

        Files are admitted, so the empty-tree guard does not fire, but no parser
        enters them — complexity, nesting, cycles and opacity never ran. Four of six
        signals unmeasured must not render as CLEAN on either channel (§10 rule 5)."""
        with tempfile.TemporaryDirectory() as tmp:
            body = "function f(x){\n" + "".join(
                f"  if(x=={i}) return {i};\n" for i in range(30)) + "}\n"
            for name, text in (("monster.js", body), ("other.ts", "export const a=1;\n")):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write(text)
            code, out, err = run("structure-report.py", tmp)
            self.assertNotIn("✅  CLEAN", out, out + err)
            self.assertIn("UNKNOWN ON THE DEEP SIGNALS", out)
            self.assertIn("0% deep-parsed", out)
            jcode, jout, _ = run("structure-report.py", tmp, "--json")
            self.assertIn("0% deep-parsed", json.loads(jout)["verdict"])

    def test_a_subject_with_nothing_analyzable_never_reads_as_clean(self):
        """Zero findings over zero files is not evidence. The prose is the deliverable
        (Law 4, director-readable output), so it must not say CLEAN while the verdict
        line says blocked — the two disagreed on the same run."""
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "PROTOCOL.md"), "w",
                      encoding="utf-8") as fh:
                fh.write("# prose only\n" * 40)
            code, out, _ = run("structure-report.py", tmp)
            self.assertEqual(code, 2, out)
            self.assertIn("blocked(no analyzable source", out)
            self.assertNotIn("✅  CLEAN", out)
            self.assertIn("NOT MEASURED", out)


class StructureRatchet(unittest.TestCase):
    """PROTOCOL §10: debt accrues through defensible increments, so the gate must
    measure DIRECTION, not level. These tests are the mechanical statement of that
    rule — without them the ratchet is prose and prose drifts."""

    def _repo(self, tmp, extra_lines=0, extra_file=None):
        body = "\n".join(f"CONST_{i} = {i}" for i in range(700 + extra_lines))
        with open(os.path.join(tmp, "god.py"), "w", encoding="utf-8") as f:
            f.write(body + "\n")
        if extra_file:
            with open(os.path.join(tmp, "new.py"), "w", encoding="utf-8") as f:
                f.write(extra_file)
        return tmp

    def _baseline(self, tmp):
        b = os.path.join(tmp, "base.json")
        code, out, _ = run("structure-report.py", "--write-baseline", b, tmp)
        self.assertEqual(code, 0, out)
        return b

    def test_unchanged_debt_holds_green(self):
        """A legacy codebase must be able to pass. An un-baselined legacy run is red
        forever, and a permanently-red gate is a disabled gate."""
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            b = self._baseline(tmp)
            code, out, err = run("structure-report.py", "--baseline", b, tmp)
            self.assertNotIn("Traceback", err)
            self.assertEqual(code, 0, out)
            self.assertIn("STRUCTURE: held(", out)

    def test_growing_an_accepted_breach_fails(self):
        """The whole point: +80 lines on a god-file is individually defensible and
        must still fail once the file's size has been frozen."""
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            b = self._baseline(tmp)
            self._repo(tmp, extra_lines=80)
            code, out, _ = run("structure-report.py", "--baseline", b, tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("STRUCTURE: regressed(", out)
            self.assertIn("worse: 1", out)

    def test_new_breach_elsewhere_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            b = self._baseline(tmp)
            nested = ["def deep(x):"] + \
                     ["    " * (i + 1) + f"if x > {i}:" for i in range(9)] + \
                     ["    " * 10 + "return x"]
            self._repo(tmp, extra_file="\n".join(nested) + "\n")
            code, out, _ = run("structure-report.py", "--baseline", b, tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("new: 1", out)

    def test_baseline_key_survives_unrelated_edits(self):
        """The ratchet key must not be a line number, or every unrelated edit shows
        up as a fresh breach and the gate becomes noise nobody reads."""
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            b = self._baseline(tmp)
            with open(os.path.join(tmp, "god.py"), encoding="utf-8") as f:
                lines = f.readlines()
            lines.insert(0, "# a new header comment, shifting every line below it\n")
            with open(os.path.join(tmp, "god.py"), "w", encoding="utf-8") as f:
                f.writelines(lines)
            code, out, _ = run("structure-report.py", "--baseline", b, tmp)
            self.assertEqual(code, 0, out)   # comment is not SLoC; nothing got worse

    def test_repaid_debt_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            b = self._baseline(tmp)
            with open(os.path.join(tmp, "god.py"), "w", encoding="utf-8") as f:
                f.write("CONST = 1\n")
            code, out, _ = run("structure-report.py", "--baseline", b, tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("repaid: 1", out)

    def test_require_debt_ledger_fails_when_debt_is_unrecorded(self):
        """§10 rule 2: a baseline with no ledger is permanent amnesty. You may only
        accept debt you wrote down, with the trigger that makes repaying it due."""
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            b = self._baseline(tmp)
            ledger = os.path.join(tmp, "DEBT_LEDGER.md")
            code, out, _ = run("structure-report.py", "--baseline", b,
                               "--debt-ledger", ledger, "--require-debt-ledger", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("unledgered-debt", out)

            with open(ledger, "w", encoding="utf-8") as f:
                f.write("| D-1 | god.py | file_lines 700 | legacy | 2x cost | "
                        "3rd edit | 2026-07-27 |\n")
            code, out, _ = run("structure-report.py", "--baseline", b,
                               "--debt-ledger", ledger, "--require-debt-ledger", tmp)
            self.assertEqual(code, 0, out)

    def test_ratchet_verdicts_satisfy_the_suites_own_linter(self):
        """Every §5 verdict this tool can emit must pass verdict-lint, or the
        enforcement floor blocks on its own output."""
        for line in ("STRUCTURE: held(accepted: 3, repaid: 0)",
                     "STRUCTURE: regressed(new: 1, worse: 2, top: file_lines) | review-needed",
                     "STRUCTURE: findings(top: embedded_language, count: 4) | review-needed"):
            code, out, _ = run("verdict-lint.py", stdin=line + "\n")
            self.assertEqual(code, 0, f"{line}\n{out}")


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

    def _clean_tree(self, tmp):
        """Two modules, one importing the other, no dead modules and no defs at all —
        so the layer dimension is the only thing a verdict can be about."""
        with open(os.path.join(tmp, "main.py"), "w", encoding="utf-8") as f:
            f.write("import helper\nVALUE = helper.NAME\n")
        with open(os.path.join(tmp, "helper.py"), "w", encoding="utf-8") as f:
            f.write('NAME = "x"\n')

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

    def test_layer_spec_matching_nothing_is_unknown_not_clean(self):
        """PROTOCOL §10 rule 5: unmeasured must never render as clean.

        A layer spec whose prefixes match no module in the tree checked
        nothing; before this test the report said '(proven) — clean'."""
        with tempfile.TemporaryDirectory() as tmp:
            # A tree with NO other findings, so the layer dimension is the only thing
            # the verdict can be about. (Real findings rightly outrank an unmeasured
            # dimension — that precedence is deliberate, so it must not be under test
            # here.)
            self._clean_tree(tmp)
            bogus = os.path.join(tmp, "bogus-layers.txt")
            with open(bogus, "w", encoding="utf-8") as fh:
                fh.write("alpha: no/such/pkg/\nbeta: other/absent/\n")
            code, out, err = run("graph-audit.py", tmp, "--layers", bogus)
            self.assertIn("UNKNOWN", out, out + err)
            self.assertNotIn("clean against declared", out)
            # The VERDICT LINE and EXIT CODE are the channels automation reads
            # (PROTOCOL §5). Honesty in the prose alone is the same defect one
            # channel over — CI and run-trace.py never see the paragraph.
            self.assertNotIn("LATENT: clean", out)
            self.assertIn("LATENT: blocked(layer spec matched 0 of 2", out)
            self.assertEqual(code, 2, out)

    def test_a_layers_file_that_parses_to_nothing_is_not_reported_as_absent(self):
        """`--layers` WAS passed; blaming the operator for not passing it hides it."""
        with tempfile.TemporaryDirectory() as tmp:
            self._clean_tree(tmp)
            empty = os.path.join(tmp, "empty-layers.txt")
            with open(empty, "w", encoding="utf-8") as fh:
                fh.write("# only a comment\n\n")
            code, out, _ = run("graph-audit.py", tmp, "--layers", empty)
            self.assertNotIn("no --layers file declared", out)
            self.assertIn("parsed to zero layers", out)
            self.assertEqual(code, 2, out)

    def test_layer_coverage_is_always_reported(self):
        """Coverage is reported even when the spec matches everything."""
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp)
            code, out, err = run("graph-audit.py", tmp, "--layers", layers)
            self.assertIn("coverage:", out, out + err)
            self.assertIn("modules classified", out)
            jcode, jout, _ = run("graph-audit.py", tmp, "--layers", layers,
                                 "--json")
            cov = json.loads(jout)["layer_coverage"]
            self.assertEqual(cov["total"], 5, jout)
            self.assertLess(cov["mapped"], cov["total"])   # main.py unmapped


class StopGate(unittest.TestCase):
    """The Stop hook had NO test coverage and CI never ran its selftest, which is how
    both root-resolution defects survived: the hook loads its rules from wherever the
    plugin is INSTALLED, while a session developing the suite edits a checkout
    elsewhere."""

    def _load(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "stop_gate_under_test", os.path.join(HERE, "stop-gate.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_selftest_passes(self):
        code, out, err = run("stop-gate.py", "--selftest")
        self.assertEqual(code, 0, out + err)
        self.assertIn("selftest passed", out)

    def test_rules_come_from_the_checkout_being_edited(self):
        """A session that ADDS a verdict state must be able to stop.

        Without this, the transcript emits the new state, the INSTALLED release's
        registry does not know it yet, the gate blocks — and the change can never be
        finished because it can never be released. Reproduced for real: a pinned
        v1.14.1 cache blocked the session that introduced `STRUCTURE: regressed`."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            fake = os.path.join(tmp, "some-checkout")
            os.makedirs(os.path.join(fake, ".claude-plugin"))
            os.makedirs(os.path.join(fake, "tools"))
            name = sg._manifest_name(sg.PLUGIN_ROOT)
            self.assertIsNotNone(name, "plugin must declare a name")
            with open(os.path.join(fake, ".claude-plugin", "plugin.json"), "w",
                      encoding="utf-8") as f:
                json.dump({"name": name, "version": "0.0.0"}, f)
            with open(os.path.join(fake, "tools", "verdict-lint.py"), "w",
                      encoding="utf-8") as f:
                f.write("REGISTRY = {}\n")
            deep = os.path.join(fake, "skills", "x")
            os.makedirs(deep)
            self.assertEqual(str(sg.suite_root(deep)), fake,
                             "a session inside a suite checkout must be governed by it")

    def _hostile_checkout(self, sg, tmp, body):
        """A directory that ASSERTS this plugin's name and ships a verdict-lint.py."""
        fake = os.path.join(tmp, "hostile")
        os.makedirs(os.path.join(fake, ".claude-plugin"))
        os.makedirs(os.path.join(fake, "tools"))
        os.makedirs(os.path.join(fake, "sub", "deep"))
        with open(os.path.join(fake, ".claude-plugin", "plugin.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"name": sg._manifest_name(sg.PLUGIN_ROOT)}, f)
        with open(os.path.join(fake, "tools", "verdict-lint.py"), "w",
                  encoding="utf-8") as f:
            f.write(body)
        return fake

    def test_a_subject_controlled_checkout_is_never_executed(self):
        """The hook must not import code from a directory cwd merely sits under.

        `suite_root` matches on a manifest `name` any directory may assert, so
        before this guard two planted files — plugin.json and tools/verdict-lint.py
        — anywhere at or above cwd got their module body exec'd as the user on
        every Stop, silently (the hook fails open). Identity by self-asserted
        string is not authority; code comes from PLUGIN_ROOT alone."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            canary = os.path.join(tmp, "canary")
            fake = self._hostile_checkout(
                sg, tmp,
                "import pathlib\n"
                f"pathlib.Path({canary!r}).write_text('executed')\n"
                "REGISTRY = {}\n")
            sg.run({"cwd": os.path.join(fake, "sub", "deep")})
            self.assertFalse(os.path.exists(canary),
                             "hostile checkout's module body was executed")

    def test_a_checkouts_new_verdict_state_still_governs_its_session(self):
        """The legitimate case survives the guard: registry read as DATA."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            fake = self._hostile_checkout(
                sg, tmp, "REGISTRY = {'NEWNOUN': {'invented'}}\n")
            extra = sg.registry_from_source(fake)
            self.assertEqual(extra.get("NEWNOUN"), {"invented"}, extra)
            tp = os.path.join(tmp, "t.jsonl")
            with open(tp, "w", encoding="utf-8") as f:
                f.write(json.dumps({"message": {
                    "role": "assistant",
                    "content": "NEWNOUN: invented(x)"}}) + "\n")
            deep = os.path.join(fake, "sub", "deep")
            self.assertEqual(
                sg.run({"cwd": deep, "transcript_path": tp}), 0,
                "a state the checkout declares must not block that checkout's session")

    def test_a_hostile_checkout_cannot_loosen_an_existing_rule(self):
        """The data hatch must be additive-only, or it disables the floor it guards.

        A directory that merely ASSERTS this plugin's name sits above many a session's
        cwd. If its REGISTRY could widen a noun this release already fixed, planting
        `GATE: {passed}` would make illegal verdict lines lint clean — switching the
        enforcement floor off for a session not developing the suite at all."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            fake = self._hostile_checkout(
                sg, tmp,
                "REGISTRY = {'GATE': {'passed'}, 'SLICE': {'done'}}\n")
            tp = os.path.join(tmp, "t.jsonl")
            with open(tp, "w", encoding="utf-8") as f:
                f.write(json.dumps({"message": {
                    "role": "assistant",
                    "content": "GATE: passed\nSLICE login: done"}}) + "\n")
            deep = os.path.join(fake, "sub", "deep")
            self.assertEqual(
                sg.run({"cwd": deep, "transcript_path": tp}), 2,
                "a planted registry widened a noun PROTOCOL already fixed")

    def test_registry_parse_evaluates_no_code(self):
        """literal_eval only: a computed REGISTRY yields {}, never execution."""
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            canary = os.path.join(tmp, "canary2")
            fake = self._hostile_checkout(
                sg, tmp,
                "import pathlib\n"
                f"REGISTRY = {{'X': pathlib.Path({canary!r}).write_text('x')}}\n")
            self.assertEqual(sg.registry_from_source(fake), {})
            self.assertFalse(os.path.exists(canary))

    def test_unrelated_directory_falls_back_to_the_installed_plugin(self):
        sg = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sg.suite_root(tmp), sg.PLUGIN_ROOT)

    def test_identity_is_the_manifest_name_not_a_directory_name(self):
        """Install path is <plugin>/<version>/ and the checkout is
        `top-tier-engineer-skill` — neither directory is named what the plugin is
        named, so keying on a directory name silently never matches."""
        sg = self._load()
        self.assertNotEqual(sg.PLUGIN_ROOT.name, sg._manifest_name(sg.PLUGIN_ROOT))

    def test_internal_error_fails_open(self):
        """A lint tool must never wedge a session on its own bug."""
        code, out, err = run("stop-gate.py", stdin="not json at all")
        self.assertEqual(code, 0, out + err)


class SuiteConsistency(unittest.TestCase):
    """The suite's self-description must match the filesystem. A current-state doc
    that names the skill count as a word (PROTOCOL, the plugin manifest) must use the
    word matching the number of skills/ dirs. Earned: 'eighteen skills' shipped into
    PROTOCOL §title while the suite had nineteen — the drift-arbiter file drifted."""

    WORDS = {16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
             20: "twenty", 21: "twenty-one", 22: "twenty-two"}

    # Every pure current-state surface that states the count. README is excluded on
    # purpose: it mixes current and historical counts ("seventeenth skill" narrates a
    # past milestone), so a strict no-neighbour check would false-fail on real history.
    SURFACES = ("PROTOCOL.md", "MAP.md",
                os.path.join(".claude-plugin", "plugin.json"),
                os.path.join(".claude-plugin", "marketplace.json"))

    def test_skill_count_matches_current_state_claims(self):
        root = os.path.dirname(HERE)
        n = sum(1 for e in os.scandir(os.path.join(root, "skills")) if e.is_dir())
        self.assertIn(n, self.WORDS, f"extend WORDS past {n} skills")
        right = self.WORDS[n]
        for rel in self.SURFACES:
            text = open(os.path.join(root, rel), encoding="utf-8").read().lower()
            self.assertIn(right, text, f"{rel} never states the {right}-skill count")
            # Phrasing-independent: a neighbour count word anywhere in a current-state
            # surface is drift, whether it reads "eighteen skills" or "eighteen wired
            # engineering skills". (The bug that shipped was the former; the manifests
            # use the latter, which an adjacency-only check would miss.)
            for k in (n - 1, n + 1):
                self.assertNotIn(self.WORDS[k], text,
                                 f"{rel} names {self.WORDS[k]}; filesystem has {n} skills")


if __name__ == "__main__":
    unittest.main()
