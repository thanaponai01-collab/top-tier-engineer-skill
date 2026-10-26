#!/usr/bin/env python3
"""
structure.py - the three stages behind structure-gate.

Each test plants the thing a stage exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import os, re, subprocess, sys, tempfile, unittest

from _helpers import SCRIPTS

S = os.path.join(SCRIPTS["structure.py"], "structure.py")
NOTES = os.path.join(".structure", "notes.md")

JS = "\n".join(
    f"  if (state.f{i}) {{\n    for (var j = 0; j < items.length; j++) {{\n"
    f"      if (items[j].kind === 'k{i}') {{\n        rows.push(items[j]);\n      }}\n    }}\n  }}"
    for i in range(8))
OPAQUE = {
    "app/page.py": f'"""Serves the page."""\n\nPAGE_JS = """\nfunction render(state) {{\n  var rows = [];\n{JS}\n'
                   '  return rows;\n}\n"""\n\n\ndef page():\n    return PAGE_JS\n',
    "app/handlers.py": "def health():\n    return {'ok': True}\n",
}
TANGLED = "def price(o):\n    t = 0\n" + "".join(
    f"    if o.get('k{i}'):\n        if o['k{i}'] > {i}:\n            t += {i}\n" for i in range(9)) + "    return t\n"
APP = {
    "app/__init__.py": "",
    "app/pricing.py": TANGLED,
    "app/models.py": "from app import store\n\n\ndef load(k):\n    return store.get(k)\n\n\ndef blank():\n    return {}\n",
    "app/store.py": "from app import models\n\n\ndef get(k):\n    return models.blank()\n",
    "web/app.js": "function go() {\n  return 1;\n}\n",
}
BLOCK = ("    number = str(inv['n']).zfill(6)\n    name = inv['c'].strip().title()\n"
         "    amount = round(float(inv['a']), 2)\n    cur = inv.get('cur', 'USD').upper()\n"
         "    status = 'paid' if inv.get('p') else 'open'\n    flag = bool(inv.get('f'))\n"
         "    note = inv.get('note', '')\n")
COPIES = {"a.py": "def rows(inv):\n" + BLOCK + "    return [number]\n",
          "b.py": "def recs(inv):\n" + BLOCK + "    return {'n': number}\n"}


def make(tmp, files):
    for rel, text in files.items():
        p = os.path.join(tmp, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


def gate(tmp, *paths, isolated=False):
    argv = [sys.executable] + (["-I"] if isolated else []) + [S, "--gate", *paths]
    p = subprocess.run(argv, cwd=tmp, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout + p.stderr


def notes(tmp, *lines):
    os.makedirs(os.path.join(tmp, ".structure"), exist_ok=True)
    with open(os.path.join(tmp, NOTES), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def read_notes(tmp):
    with open(os.path.join(tmp, NOTES), encoding="utf-8") as fh:
        return fh.read()


class Measure(unittest.TestCase):
    def test_nothing_to_measure_is_blocked_not_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {"docs/readme.md": "hello\n"})
            code, out = gate(tmp, "docs")
            self.assertEqual(code, 1, out)
            self.assertIn("STAGE 1 measure", out)
            self.assertIn("blocked, not clean", out)

    def test_a_missing_path_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = gate(tmp, "nowhere")
            self.assertEqual(code, 1)
            self.assertIn("nowhere: not found", out)

    def test_runs_under_python_isolated_mode(self):
        """`python -I` drops the script's folder from sys.path; an agent ran it that way and the
        old report died on its own import."""
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as plain:
            make(tmp, OPAQUE)
            make(plain, OPAQUE)
            code, out = gate(tmp, "app", isolated=True)
            self.assertNotIn("ModuleNotFoundError", out)
            share = re.search(r"(\d+(?:\.\d+)?)% entered by a parser", out)
            self.assertIsNotNone(share, out)
            # the same share a normal run measures, not just a number somewhere in the output
            self.assertIn(f"{share.group(1)}% entered by a parser", gate(plain, "app")[1])
            self.assertLess(float(share.group(1)), 50)
            self.assertIn("STAGE 1 measure: the share a parser entered is known: holds", out)

    def test_the_bare_report_runs_under_python_isolated_mode_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, OPAQUE)
            report = os.path.join(SCRIPTS["structure-report.py"], "structure-report.py")
            p = subprocess.run([sys.executable, "-I", report, "app"], cwd=tmp, capture_output=True,
                               text=True, encoding="utf-8")
            self.assertNotIn("ModuleNotFoundError", p.stdout + p.stderr)
            self.assertIn("opaque_code", p.stdout)

    def test_from_package_import_module_cycle_is_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, APP)
            gate(tmp, "app", "web")
            self.assertIn("- cycle: models, store | cost:", read_notes(tmp))

    def test_one_copied_block_is_one_item(self):
        """A 7-line copy is two overlapping 6-line windows; it must ask for one note, not two."""
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, COPIES)
            gate(tmp, "a.py", "b.py")
            self.assertEqual(read_notes(tmp).count("| cost:"), 1, read_notes(tmp))

    def test_other_skills_state_is_not_measured_as_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {"app.py": "def f():\n    return 1\n", ".debug/before/app.py": TANGLED})
            gate(tmp, ".")
            self.assertNotIn("price", read_notes(tmp))


class Account(unittest.TestCase):
    def test_the_gate_appends_a_slot_for_every_item_and_leaves_them_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, OPAQUE)
            code, out = gate(tmp, "app")
            text = read_notes(tmp)
            self.assertIn("- paths: app", text)
            self.assertIn("- app/page.py:4 | read: [[fill", text)
            self.assertIn("- verdict: [[fill", text)
            self.assertEqual(code, 1)
            self.assertIn("app/page.py:4: the slot is still empty", out)
            gate(tmp)
            self.assertEqual(read_notes(tmp).count("app/page.py:4"), 1, "slots are appended once")

    def test_a_reading_must_count_something(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, OPAQUE)
            notes(tmp, "- paths: app", "- app/page.py:4 | read: looks fine", "- verdict: in places")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("`read:` says what you counted", out)

    def test_unentered_code_takes_read_or_unknown_not_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, OPAQUE)
            notes(tmp, "- paths: app", "- app/page.py:4 | cost: 8 blocks", "- verdict: in places")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("takes `read:` or `unknown:`", out)

    def test_a_finding_takes_cost_or_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {"p.py": TANGLED})
            notes(tmp, "- paths: p.py", "- p.py::price | read: 9 branches", "- verdict: in places")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("a finding takes `cost:", out)

    def test_a_note_on_something_not_measured_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, OPAQUE)
            notes(tmp, "- paths: app", "- app/page.py:4 | read: 8 copies of one block",
                  "- app/gone.py::old | cost: none: removed", "- verdict: in places")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("app/gone.py::old: noted, but not measured now", out)

    def test_a_folder_note_covers_files_with_no_parser_under_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {"app.py": "def f():\n    return 1\n", "web/a.js": "var a = 1;\n", "web/b.js": "var b = 2;\n"})
            notes(tmp, "- paths: .", "- web/ | read: 2 one-line files", "- verdict: no")
            code, out = gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("STRUCTURE-GATE: done", out)


class Answer(unittest.TestCase):
    def test_no_is_refused_over_code_in_a_string_even_once_read(self):
        """The trap: the entered 5% is simple, the 95% nobody can test is not clean."""
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, OPAQUE)
            notes(tmp, "- paths: app", "- app/page.py:4 | read: 8 copies of one 7-line block", "- verdict: no")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("no linter or test can reach it", out)

    def test_no_is_refused_over_unknown_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {"app.py": "def f():\n    return 1\n", "web/a.js": "var a = 1;\n"})
            notes(tmp, "- paths: .", "- web/a.js | unknown: did not open it", "- verdict: no")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("unknown is not clean", out)

    def test_no_is_refused_while_a_finding_has_a_cost_and_allowed_once_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {"p.py": TANGLED})
            notes(tmp, "- paths: p.py", "- p.py::price | cost: every rule is one more branch", "- verdict: no")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("`no` while findings stand", out)
            notes(tmp, "- paths: p.py", "- p.py::price | none: a flat rule table, one branch per rule",
                  "- verdict: no")
            code, out = gate(tmp)
            self.assertEqual(code, 0, out)

    def test_yes_needs_something_that_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {"app.py": "def f():\n    return 1\n"})
            notes(tmp, "- paths: app.py", "- verdict: yes")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("`yes` but nothing measured", out)

    def test_an_unfilled_verdict_slot_asks_for_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {"app.py": "def f():\n    return 1\n"})
            code, out = gate(tmp, "app.py")
            self.assertEqual(code, 1)
            self.assertIn("no verdict. Set `- verdict:", out)

    def test_a_verdict_must_be_one_of_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {"app.py": "def f():\n    return 1\n"})
            notes(tmp, "- paths: app.py", "- verdict: mostly")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("is not one of", out)

    def test_done_answer_gives_the_measured_share_before_the_first_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, OPAQUE)
            notes(tmp, "- paths: app", "- app/page.py:4 | read: 8 copies of one 7-line block",
                  "- verdict: in places")
            code, out = gate(tmp)
            self.assertEqual(code, 0, out)
            answer = out[out.index("ANSWER"):]
            self.assertLess(answer.index("% entered by a parser"), answer.index("| signal |"))
            self.assertIn("unknown, not clean", answer)
            self.assertIn("read by hand: 8 copies", answer)
            self.assertIn("[[fill:", answer)
            self.assertRegex(out, r"STRUCTURE-GATE: done\(\d+(\.\d)?% entered, 0 findings, 1 unentered: 1 read")


class SharedState(unittest.TestCase):
    def test_verify_loop_does_not_scan_the_notes_folder(self):
        sys.path.insert(0, SCRIPTS["verify.py"])
        try:
            import verify
            self.assertIn(".structure", verify.SKIP_DIRS)
        finally:
            sys.path.remove(SCRIPTS["verify.py"])


if __name__ == "__main__":
    unittest.main()
