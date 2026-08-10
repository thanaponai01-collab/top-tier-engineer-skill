#!/usr/bin/env python3
"""structure-report.py — the spaghetti alarm, coverage honesty, and the debt ratchet."""
import json, os, tempfile, unittest
from _helpers import run


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


if __name__ == "__main__":
    unittest.main()
