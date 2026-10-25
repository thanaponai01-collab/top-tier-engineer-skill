#!/usr/bin/env python3
"""
debug.py - the reproduction, the two-way proof and the leave stage behind debug-protocol.

Each test plants the thing a stage exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import json, os, tempfile, unittest

from _helpers import run

APP = {
    "parse.py": ("import csv\n\n\ndef parse_amount(value):\n    return int(float(value))\n\n\n"
                 "def load(path):\n    with open(path, newline='', encoding='utf-8') as fh:\n"
                 "        return [{'amount': parse_amount(r['amount'])} for r in csv.DictReader(fh)]\n"),
    "totals.py": "def total(rows):\n    return sum(row['amount'] for row in rows)\n",
    "report.py": ("from parse import load\nfrom totals import total\n\n"
                  "if __name__ == '__main__':\n    print(f'Total: {total(load(\"data.csv\"))}')\n"),
    "data.csv": "id,amount\n1,10.50\n2,20.25\n3,11.60\n",
    "test_totals.py": ("import unittest\nfrom totals import total\n\n\nclass T(unittest.TestCase):\n"
                       "    def test_adds(self):\n        self.assertEqual(total([{'amount': 10}, {'amount': 20}]), 30)\n"),
}
REPRO = ["--repro", "python report.py", "--wrong", "Total: 41", "--right", "Total: 42.35"]
CAUSE = ["--prove", "parse.py:5", "--as", "return float(value)", "--why", "parse_amount drops the cents"]
REGRESS_TEST = ("import unittest\nfrom parse import load\n\n\nclass P(unittest.TestCase):\n"
                "    def test_cents(self):\n        self.assertEqual(load('data.csv')[0]['amount'], 10.5)\n")


def make(tmp, files=APP):
    for rel, text in files.items():
        p = os.path.join(tmp, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


def edit(tmp, rel, old, new):
    p = os.path.join(tmp, *rel.split("/"))
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    assert old in text, (rel, old)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.replace(old, new))


def ledger(tmp):
    with open(os.path.join(tmp, ".debug", "state.json"), encoding="utf-8") as fh:
        return json.load(fh)


def gate(tmp, *extra):
    code, out, err = run("debug.py", tmp, "--gate", *extra)
    return code, out + err


class Reproduce(unittest.TestCase):
    def test_nothing_reproduced_keeps_stage_one_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("STAGE 1 reproduce: the failure shows on demand: open", out)

    def test_a_run_that_does_not_show_the_wrong_text_is_not_a_reproduction(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, _ = run("debug.py", tmp, "--repro", "python report.py", "--wrong", "Total: 40",
                               "--right", "Total: 42.35")
            self.assertEqual(code, 1, out)
            self.assertIn("not reproduced", out)
            self.assertIn("did not show the failure", gate(tmp)[1])

    def test_the_code_as_reproduced_is_kept_however_the_tree_moves(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            self.assertEqual(run("debug.py", tmp, *REPRO)[0], 0)
            edit(tmp, "parse.py", "int(float(value))", "float(value)")
            run("debug.py", tmp, *REPRO)
            with open(os.path.join(tmp, ".debug", "before", "parse.py"), encoding="utf-8") as fh:
                self.assertIn("int(float(value))", fh.read())
            self.assertTrue(ledger(tmp)["repro"]["wrong_seen"])


class Prove(unittest.TestCase):
    def test_only_taking_the_cause_out_proves_it_and_dead_ends_are_kept(self):
        """Rounding where the number shows leaves 41: refuted, kept in the table. The parse line is proven."""
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            code, out, _ = run("debug.py", tmp, "--prove", "totals.py:2", "--as",
                               "return round(sum(row['amount'] for row in rows), 2)", "--why", "sum loses precision")
            self.assertEqual(code, 1, out)
            self.assertIn("PROVE: refuted", out)
            code, out, _ = run("debug.py", tmp, *CAUSE)
            self.assertEqual(code, 0, out)
            self.assertEqual([e["verdict"] for e in ledger(tmp)["experiments"]], ["refuted", "proven"])
            code, out = gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("| 1 | sum loses precision", out)
            self.assertIn("Cause, proven both ways: parse.py:5 in `parse_amount`", out)

    def test_a_replacement_that_types_the_right_answer_proves_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            code, out, _ = run("debug.py", tmp, "--prove", "report.py:5", "--as", "print('Total: 42.35')",
                               "--why", "the report is wrong")
            self.assertEqual(code, 2, out)
            self.assertIn("spells the right answer", out)
            self.assertNotIn("experiments", ledger(tmp))

    def test_the_right_text_beside_the_wrong_one_is_not_a_proof(self):
        """A change that adds the right figure while the wrong one still prints has not removed the cause."""
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            code, out, _ = run("debug.py", tmp, "--prove", "report.py:5", "--as",
                               "print(f'Total: {total(load(\"data.csv\"))}'); print('Total: 42' + '.35')",
                               "--why", "the report prints the wrong figure")
            self.assertEqual(code, 1, out)
            self.assertIn("still shows 'Total: 41'", out)

    def test_proof_runs_on_the_code_as_reproduced_not_the_fixed_tree(self):
        """Fixed in place first: the experiment still replaces the line in the broken code, so the
        with-cause side is the real failure."""
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            edit(tmp, "parse.py", "int(float(value))", "float(value)")
            run("debug.py", tmp, *CAUSE)
            self.assertEqual(ledger(tmp)["experiments"][0]["was"].strip(), "return int(float(value))")

    def test_the_suite_receipt_says_no_test_enters_the_cause(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            run("debug.py", tmp, *CAUSE)
            out = gate(tmp)[1]
            self.assertIn("passes on the broken code; no test enters `parse_amount`", out)

    def test_past_the_budget_the_gate_asks_for_the_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            for i in range(5):
                run("debug.py", tmp, "--prove", "totals.py:2", "--as", f"return sum(r['amount'] for r in rows) + {i}",
                    "--why", f"guess {i}")
            out = gate(tmp)[1]
            self.assertIn("past the budget", out)
            self.assertIn("two refuted experiments in totals.py", out)


class Leave(unittest.TestCase):
    def test_a_probe_edit_left_behind_keeps_diagnosis_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            edit(tmp, "totals.py", "return sum", "print(rows)\n    return sum")
            code, out = gate(tmp)
            self.assertIn("no fixing while diagnosing", out)
            edit(tmp, "totals.py", "print(rows)\n    return sum", "return sum")
            run("debug.py", tmp, *CAUSE)
            code, out = gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("diagnosis only", out)

    def test_a_fix_where_the_symptom_shows_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            run("debug.py", tmp, *CAUSE)
            edit(tmp, "report.py", "print(f'Total: {total(load(\"data.csv\"))}')", "print('Total: 42.35')")
            out = gate(tmp)[1]
            self.assertIn("Fix it where it starts", out)

    def test_a_fix_needs_a_check_that_fails_with_the_cause_put_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            run("debug.py", tmp, *CAUSE)
            edit(tmp, "parse.py", "int(float(value))", "float(value)")
            out = gate(tmp)[1]
            self.assertIn("no regression check", out)
            code, out = gate(tmp, "--regress", "python -m unittest test_totals")
            self.assertIn("cannot see this bug", out)
            make(tmp, {"test_parse.py": REGRESS_TEST})
            code, out = gate(tmp, "--regress", "python -m unittest test_parse")
            self.assertEqual(code, 0, out)
            self.assertIn("fails with the cause put back", out)

    def test_a_check_that_ran_no_tests_does_not_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            run("debug.py", tmp, *REPRO)
            run("debug.py", tmp, *CAUSE)
            edit(tmp, "parse.py", "int(float(value))", "float(value)")
            # `|| true`: on Python before 3.12 an empty discover exits 0, and that must not pass either.
            out = gate(tmp, "--regress", "python -m unittest discover -p 'nothing_*.py' || true")[1]
            self.assertIn("ran no tests", out)

    def test_with_verify_md_the_cause_file_must_be_mapped(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"VERIFY.md": "# Checks\n", "test_parse.py": REGRESS_TEST}))
            run("debug.py", tmp, *REPRO)
            run("debug.py", tmp, *CAUSE)
            edit(tmp, "parse.py", "int(float(value))", "float(value)")
            out = gate(tmp, "--regress", "python -m unittest test_parse")[1]
            self.assertIn("VERIFY.md maps no check over parse.py", out)
            self.assertIn("- path: parse.py\n      - test: `python -m unittest test_parse`", out)
            edit(tmp, "VERIFY.md", "# Checks\n", "# Checks\n\n## Parse\n- path: parse.py\n")
            code, out = gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("DEBUG-GATE: done(1 proven of 1 experiments, fixed and held)", out)


if __name__ == "__main__":
    unittest.main()
