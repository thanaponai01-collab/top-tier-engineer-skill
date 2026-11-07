"""untangle.py - the history-ranked scope, the baseline and the behavior check behind untangle.

Each test plants the thing a stage exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import os, shutil, subprocess, tempfile, unittest

from _helpers import run

RATE = "RATE = 0.10\n"
FILES = {
    "app/__init__.py": "",
    "app/pricing.py": "RATE = 0.10\n\n\ndef total(x):\n    return round(x * (1 - RATE), 2)\n",
    "app/export.py": "RATE = 0.10\n\n\ndef row(x):\n    return f'{x:.2f},{round(x * (1 - RATE), 2):.2f}'\n",
    "app/invoice.py": "from app.pricing import total\n\n\ndef line(x):\n    return f'TOTAL {total(x)}'\n",
    "app/util.py": "def pad(s, n):\n    return s.ljust(n)\n",
    "tests/__init__.py": "",
    "tests/test_app.py": ("import unittest\nfrom app import export, invoice, pricing\n\n\n"
                          "class T(unittest.TestCase):\n"
                          "    def test_total(self):\n        self.assertEqual(pricing.total(100), 90.0)\n"
                          "    def test_row(self):\n        self.assertEqual(export.row(100), '100.00,90.00')\n"
                          "    def test_line(self):\n        self.assertEqual(invoice.line(100), 'TOTAL 90.0')\n"),
}
TESTS = "python -m unittest discover -s tests -t ."
GUARD_TEST = ("import unittest\nfrom app import export, pricing, rates\n\n\n"
              "class OneRate(unittest.TestCase):\n"
              "    def test_one_rate(self):\n"
              "        self.assertIs(export.RATE, rates.RATE)\n        self.assertIs(pricing.RATE, rates.RATE)\n")
GUARD = "python -m unittest tests/test_one_rate.py"
PAIR = "app/export.py + app/pricing.py"
MARK = "# untangle: known bug: "
SCOPE = {"hotspot app/pricing.py": "target: 4 fix commits, each also had to touch export",
         "hotspot app/export.py": "target: same 4 fixes",
         "hotspot app/util.py": "skip: one added helper, nothing fixed",
         f"pair {PAIR}": "target: the rate is copied in both"}


def write(root, rel, text):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def edit(root, rel, old, new):
    p = os.path.join(root, *rel.split("/"))
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    assert old in text, (rel, old)
    write(root, rel, text.replace(old, new))


def git(root, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                          cwd=root, capture_output=True, text=True)


def commit(root, msg):
    git(root, "add", "-A")
    git(root, "commit", "-qm", msg)


def make(root, red_test=False):
    """A repo whose history fixes the discount four times, each in pricing and in export."""
    for rel, text in FILES.items():
        write(root, rel, text)
    if red_test:
        write(root, "tests/test_red.py", "import unittest\n\n\nclass R(unittest.TestCase):\n"
                                         "    def test_rounding(self):\n        self.assertEqual(1, 2)\n")
    git(root, "init", "-q")
    commit(root, "shop totals, invoices and export")
    for i, (old, new) in enumerate([("0.10", "0.08"), ("0.08", "0.12"), ("0.12", "0.09"), ("0.09", "0.10")]):
        edit(root, "app/pricing.py", old, new)
        edit(root, "app/export.py", old, new)
        commit(root, f"fix: discount {i} missed the export")
    write(root, "app/util.py", FILES["app/util.py"] + "\n\ndef cut(s, n):\n    return s[:n]\n")
    commit(root, "add cut helper")


def notes(root):
    with open(os.path.join(root, ".untangle", "notes.md"), encoding="utf-8") as fh:
        return fh.read()


def fill(root, **lines):
    text = notes(root)
    for key, value in lines.items():
        start = text.index(f"- {key}: ")
        end = text.index("\n", start)
        text = text[:start] + f"- {key}: {value}" + text[end:]
    write(root, ".untangle/notes.md", text)


def add_notes(root, text):
    write(root, ".untangle/notes.md", notes(root) + text)


def move_lines(guard=GUARD, unit=PAIR):
    return (f"- also app/rates.py: serves app/pricing.py\n"
            f"- move {unit}: rate from app/rates.py | guard: {guard}\n")


def red_key(root):
    red = next(l for l in notes(root).splitlines() if l.startswith("- red "))
    return red[2:].split(": [[fill")[0]


def gate(root, *extra, cmd=TESTS):
    code, out, err = run("untangle.py", root, "--gate", "--run", cmd, *extra)
    return code, out + err


def untangle(root):
    write(root, "app/rates.py", RATE)
    edit(root, "app/pricing.py", "RATE = 0.10\n", "from app.rates import RATE\n")
    edit(root, "app/export.py", "RATE = 0.10\n", "from app.rates import RATE\n")
    write(root, "tests/test_one_rate.py", GUARD_TEST)


class Untangle(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="untangle-test-")

    def tearDown(self):
        git(self.root, "worktree", "prune")
        shutil.rmtree(self.root, ignore_errors=True)

    # ---- ranking

    def test_needs_git(self):
        write(self.root, "a.py", "x = 1\n")
        code, out, _ = run("untangle.py", self.root)
        self.assertEqual(code, 2)
        self.assertIn("needs git", out)

    def test_ranks_the_fixed_files_and_the_pair_that_changes_together(self):
        make(self.root)
        code, out, _ = run("untangle.py", self.root)
        self.assertEqual(code, 0, out)
        lines = out.splitlines()
        hot = lines[lines.index("HOTSPOTS (commits, fix commits):") + 1]
        self.assertIn("4 fixes  FIX-HEAVY", hot)
        self.assertIn(f"{PAIR}  5", out)
        self.assertNotIn("app/invoice.py", out.split("PAIRS")[0], "a file changed once is no hotspot")

    def test_a_file_untouched_in_the_recent_commits_is_not_ranked(self):
        make(self.root)
        code, out, _ = run("untangle.py", self.root, "--recent", "1")
        self.assertEqual(code, 0, out)
        self.assertIn("app/util.py", out)
        self.assertNotIn("app/pricing.py", out)

    # ---- stage 1

    def test_baseline_refuses_a_tree_that_already_changed(self):
        make(self.root)
        edit(self.root, "app/pricing.py", "round(", "round(0 + ")
        code, out = gate(self.root)
        self.assertEqual(code, 1)
        self.assertIn("STAGE 1 OPEN", out)
        self.assertIn("app/pricing.py", out)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".untangle", "state.json")))

    def test_baseline_refuses_a_command_that_ran_no_tests(self):
        make(self.root)
        for cmd in ("python -m unittest discover -s app -p nothing_*.py",
                    'python -c "import sys; sys.exit(4)"'):
            code, out = gate(self.root, cmd=cmd)
            self.assertEqual(code, 1, out)
            self.assertIn("Fix the command (nothing was recorded)", out)
            self.assertFalse(os.path.exists(os.path.join(self.root, ".untangle", "state.json")))

    def test_every_hotspot_and_pair_needs_target_or_skip(self):
        make(self.root)
        code, out = gate(self.root)
        self.assertEqual(code, 1)
        self.assertIn("hotspot app/util.py: say `target: <commits>` or `skip: <why>`", out)
        self.assertIn(f"pair {PAIR}", out)
        self.assertIn("- hotspot app/pricing.py: [[fill", notes(self.root))

    def test_a_fix_heavy_hotspot_cannot_be_skipped_without_a_guard_that_covers_it(self):
        make(self.root)
        gate(self.root)
        fill(self.root, **{**SCOPE, "hotspot app/pricing.py": "skip: fixes are local to the file"})
        code, out = gate(self.root)
        self.assertIn("hotspot app/pricing.py: 4 of its 5 commits are fixes", out)
        write(self.root, "tests/test_other.py", "import unittest\n")
        fill(self.root, **{"hotspot app/pricing.py": "skip: local | guard: python -m unittest tests/test_other.py"})
        code, out = gate(self.root)
        self.assertIn("names no test file that mentions pricing", out)
        fill(self.root, **{"hotspot app/pricing.py": "skip: local | guard: python -m unittest tests/test_app.py"})
        code, out = gate(self.root)
        self.assertNotIn("hotspot app/pricing.py", out)

    def test_a_red_test_at_the_baseline_must_be_classified_and_a_bug_marked_in_the_code(self):
        make(self.root, red_test=True)
        gate(self.root)
        fill(self.root, **SCOPE)
        code, out = gate(self.root)
        self.assertIn("STAGE 1 OPEN: red", out)
        self.assertIn("test_rounding", out)
        key = red_key(self.root)
        fill(self.root, **{key: "bug: rounding is wrong"})
        code, out = gate(self.root)
        self.assertIn("a bug needs the file:line of the fault", out)
        fill(self.root, **{key: "bug: app/invoice.py:5 formats before rounding"})
        code, out = gate(self.root)
        self.assertIn("comment within 3 lines of app/invoice.py:5", out)
        edit(self.root, "app/invoice.py", "    return f'TOTAL",
             f"    {MARK}TOTAL is unrounded\n    return f'TOTAL")
        code, out = gate(self.root)
        self.assertNotIn("STAGE 1 OPEN", out)
        self.assertNotIn("app/invoice.py changed but is no target", out, "the marker alone is no change")

    def test_reds_failing_in_one_file_with_one_message_share_a_slot(self):
        make(self.root)
        fake = ('python -c "'
                "print('FAILED t/test_box.py::a[1] - ModuleNotFoundError: no uharfbuzz');"
                "print('FAILED t/test_box.py::a[2] - ModuleNotFoundError: no uharfbuzz');"
                "print('FAILED t/test_cue.py::b - AssertionError');"
                "print('2 passed, 3 failed in 1s');raise SystemExit(1)\"")
        gate(self.root, cmd=fake)
        reds = [l for l in notes(self.root).splitlines() if l.startswith("- red ")]
        self.assertEqual(len(reds), 2, reds)
        self.assertTrue(any("t/test_box.py::* (ModuleNotFoundError: no uharfbuzz)" in l for l in reds), reds)

    # ---- stage 2

    def test_a_changed_file_that_is_no_target_keeps_stage_two_open(self):
        make(self.root)
        gate(self.root)
        fill(self.root, **SCOPE)
        untangle(self.root)
        write(self.root, "app/invoice.py", FILES["app/invoice.py"] + "# tidy\n")
        add_notes(self.root, f"- move {PAIR}: rate from app/rates.py | guard: {GUARD}\n")
        code, out = gate(self.root)
        self.assertEqual(code, 1)
        self.assertIn("app/invoice.py changed but is no target", out)
        self.assertIn("app/rates.py changed but is no target", out)

    def test_a_guard_that_passes_on_the_old_code_is_refused(self):
        make(self.root)
        gate(self.root)
        fill(self.root, **SCOPE)
        untangle(self.root)
        add_notes(self.root, move_lines(guard="python -m unittest tests/test_app.py"))
        code, out = gate(self.root)
        self.assertEqual(code, 1)
        self.assertIn(f"guard for {PAIR} also passes on the committed tree", out)

    def test_a_targeted_pair_takes_one_move_and_its_files_none_of_their_own(self):
        make(self.root)
        gate(self.root)
        fill(self.root, **SCOPE)
        untangle(self.root)
        add_notes(self.root, "- also app/rates.py: serves app/pricing.py\n")
        code, out = gate(self.root)
        self.assertIn(f"move {PAIR}: say what changed", out)
        self.assertNotIn("move app/pricing.py:", out)
        self.assertNotIn("move app/export.py:", out)

    def test_a_move_that_names_no_change_is_refused(self):
        make(self.root)
        gate(self.root)
        fill(self.root, **{**SCOPE, "hotspot app/util.py": "target: two helpers that should be one"})
        untangle(self.root)
        add_notes(self.root, move_lines() + "- move app/util.py: file unchanged | guard: none: nothing\n")
        code, out = gate(self.root)
        self.assertIn("move app/util.py: names no change", out)

    # ---- stage 3

    def test_a_test_green_at_the_baseline_and_red_after_keeps_stage_three_open(self):
        make(self.root)
        gate(self.root)
        fill(self.root, **SCOPE)
        untangle(self.root)
        write(self.root, "app/rates.py", "RATE = 0.11\n")
        add_notes(self.root, move_lines())
        code, out = gate(self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("STAGE 3 OPEN", out)
        self.assertIn("green at the baseline, red now", out)

    def test_the_whole_untangle_passes_and_answers(self):
        make(self.root, red_test=True)
        gate(self.root)
        fill(self.root, **SCOPE)
        fill(self.root, **{red_key(self.root): "bug: tests/test_red.py:6 asserts 1 == 2"})
        edit(self.root, "tests/test_red.py", "        self.assertEqual(1, 2)",
             f"        {MARK}asserts 1 == 2\n        self.assertEqual(1, 2)")
        untangle(self.root)
        add_notes(self.root, move_lines())
        code, out = gate(self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("UNTANGLE-GATE: done", out)
        self.assertLess(out.index("Real faults found"), out.index("Untangled:"))
        self.assertIn("app/util.py: one added helper", out)

    def test_an_unchanged_tree_reuses_the_suite_run(self):
        log = self.root + "-runs.log"
        counted = f"python -c \"open(r'{log}', 'a').write('x')\" && {TESTS}"
        make(self.root)
        gate(self.root, cmd=counted)
        fill(self.root, **SCOPE)
        untangle(self.root)
        add_notes(self.root, move_lines())
        for _ in range(2):
            code, out = gate(self.root, cmd=counted)
            self.assertEqual(code, 0, out)
        with open(log, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "xx", "the baseline once, the changed tree once")
        os.remove(log)

    def test_the_same_commands_must_rerun(self):
        make(self.root)
        gate(self.root)
        code, out = gate(self.root, cmd="python -c pass")
        self.assertEqual(code, 1)
        self.assertIn("differs from the baseline", out)

    def test_nothing_to_untangle_when_every_hotspot_is_skipped(self):
        make(self.root)
        gate(self.root)
        cover = " | guard: python -m unittest tests/test_app.py"
        fill(self.root, **{k: "skip: settled since" + (cover if k.endswith(("pricing.py", "export.py")) else "")
                           for k in SCOPE})
        code, out = gate(self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("Nothing here needs untangling", out)


if __name__ == "__main__":
    unittest.main()
