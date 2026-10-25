#!/usr/bin/env python3
"""
evolve.py - the kept tree, the readers of a change and the hold stage behind evolve-maintain.

Each test plants the thing a guard exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import json, os, tempfile, unittest

from _helpers import run

APP = {
    "model.py": ("class Order:\n    def __init__(self, lines):\n        self.lines = lines\n\n"
                 "    @property\n    def total(self):\n        return sum(self.lines)\n\n"
                 "    def add(self, n):\n        self.lines.append(n)\n"),
    "refunds.py": ("def refund(order, n):\n    print('before', order.total)\n    order.lines.append(-n)\n"
                   "    return order.total\n"),
    "backup.py": ("import json\n\n\ndef backup(order, path):\n    worth = order.total\n"
                  "    with open(path, 'w') as fh:\n        json.dump(order, fh, default=vars, sort_keys=True)\n"
                  "    return worth\n"),
    "cli.py": ("import sys\nfrom model import Order\nfrom refunds import refund\nfrom backup import backup\n\n"
               "o = Order([5, 7])\nif sys.argv[1] == 'refund':\n    print('now', refund(o, 5))\n"
               "elif sys.argv[1] == 'backup':\n    print('worth', backup(o, sys.argv[2]))\n"
               "else:\n    print('total', o.total)\n"),
    "tests/test_model.py": ("import unittest\nfrom model import Order\n\n\nclass T(unittest.TestCase):\n"
                            "    def test_total(self):\n        self.assertEqual(Order([1, 2]).total, 3)\n"),
}
CACHE = ("    @property\n    def total(self):\n        return sum(self.lines)\n",
         "    @property\n    def total(self):\n        if not hasattr(self, '_t'):\n"
         "            self._t = sum(self.lines)\n        return self._t\n")
# a cache that does not leak into vars() and sees every append
GOOD_CACHE = ("    @property\n    def total(self):\n        return sum(self.lines)\n",
              "    @property\n    def total(self):\n        key = tuple(self.lines)\n"
              "        if _CACHE.get(id(self), (None,))[0] != key:\n"
              "            _CACHE[id(self)] = (key, sum(self.lines))\n        return _CACHE[id(self)][1]\n")


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


def notes(tmp):
    with open(os.path.join(tmp, ".evolve", "notes.md"), encoding="utf-8") as fh:
        return fh.read()


def note(tmp, line):
    p = os.path.join(tmp, ".evolve", "notes.md")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    key = line.split(":", 1)[0]
    try:
        with open(p, encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if not ln.startswith(key + ":")]
    except OSError:
        lines = []
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines + [line]) + "\n")


def E(tmp, *args):
    return run("evolve.py", tmp, *args)


def gate(tmp):
    code, out, err = E(tmp, "--gate")
    return code, out + err


def ready(tmp, runs=("python cli.py total", "python cli.py refund", "python cli.py backup b.json")):
    make(tmp)
    E(tmp)
    for cmd in runs:
        code, out, err = E(tmp, "--run", cmd)
        assert code == 0, out + err


class Before(unittest.TestCase):
    def test_first_call_keeps_the_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, _ = E(tmp)
            self.assertEqual(code, 0)
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".evolve", "before", "model.py")))
            self.assertIn("Kept the tree", out)

    def test_no_run_recorded_leaves_stage_one_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            E(tmp)
            edit(tmp, "model.py", *CACHE)
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("STAGE 1", out)
            self.assertRegex(out, r"STAGE 1 [^\n]*open")

    def test_a_run_added_after_the_edit_records_the_old_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            E(tmp)
            edit(tmp, "model.py", "return sum(self.lines)", "return sum(self.lines) + 1")
            code, out, _ = E(tmp, "--run", "python cli.py total")
            self.assertEqual(code, 0, out)
            self.assertIn("total 12", out)

    def test_a_path_outside_the_repo_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as other:
            make(tmp)
            code, out, _ = E(tmp, "--run", f"python cli.py backup {os.path.join(other, 'b.json')}")
            self.assertEqual(code, 2)
            self.assertIn("outside the repo", out)

    def test_a_url_path_argument_is_not_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"app.py": "import sys\nprint(sys.argv[1])\n"}))
            code, out, _ = E(tmp, "--run", "python app.py /v1/export")
            self.assertEqual(code, 0, out)
            # Git Bash would turn it into C:/Program Files/Git/v1/export; the run must see it as typed
            self.assertIn("| /v1/export", out)

    def test_a_run_that_varies_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"clock.py": "import time\nprint(time.perf_counter_ns())\n"}))
            code, out, _ = E(tmp, "--run", "python clock.py")
            self.assertEqual(code, 1)
            self.assertIn("different the second time", out)

    def test_test_timings_do_not_count_as_variation(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"timed.py": ("import time\nimport model\n"
                                                "print(f'Ran 3 tests in {time.perf_counter_ns() % 997}.002s')\n")}))
            code, out, _ = E(tmp, "--run", "python timed.py")
            self.assertEqual(code, 0, out)

    def test_a_run_that_enters_no_repo_code_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, _ = E(tmp, "--run", "echo hi")
            self.assertEqual(code, 1)
            self.assertIn("entered no code", out)


class Reach(unittest.TestCase):
    def test_a_reader_no_run_entered_is_listed_and_slotted(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp, runs=("python cli.py total",))
            edit(tmp, "model.py", *GOOD_CACHE)
            edit(tmp, "model.py", "class Order:", "_CACHE = {}\n\n\nclass Order:")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("refunds.py::refund (reads total)", out)
            self.assertIn("backup.py::backup", out)
            self.assertIn("- refunds.py::refund: [[fill", notes(tmp))

    def test_tests_are_not_readers(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp, runs=("python cli.py total",))
            edit(tmp, "model.py", *CACHE)
            _, out = gate(tmp)
            self.assertNotIn("tests/test_model.py", out)

    def test_out_must_say_why(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp, runs=("python cli.py total", "python cli.py refund"))
            edit(tmp, "model.py", *CACHE)
            gate(tmp)
            note(tmp, "- backup.py::backup: out: fine")
            _, out = gate(tmp)
            self.assertIn("says too little", out)

    def test_out_that_claims_a_run_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp, runs=("python cli.py total", "python cli.py refund"))
            edit(tmp, "model.py", *CACHE)
            gate(tmp)
            note(tmp, "- backup.py::backup: out: covered by the cli run I did")
            _, out = gate(tmp)
            self.assertIn("says a run or test covers it", out)

    def test_a_note_for_something_not_a_reader_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp)
            edit(tmp, "model.py", *GOOD_CACHE)
            edit(tmp, "model.py", "class Order:", "_CACHE = {}\n\n\nclass Order:")
            note(tmp, "- nowhere.py::f: out: this file does not exist at all")
            _, out = gate(tmp)
            self.assertIn("not a reader of this change", out)

    def test_a_config_line_naming_a_removed_route_is_a_reader_until_a_run_opens_it(self):
        files = {
            "app.py": ("ROUTES = {'/v1/export': lambda: 'v1', '/v2/export': lambda: 'v2'}\n\n\n"
                       "def dispatch(url):\n    h = ROUTES.get(url)\n    return h() if h else 404\n"),
            "jobs.yaml": "- url: /v1/export\n- url: /v2/export\n",
            "scheduler.py": ("import os\nimport app\n\nHERE = os.path.dirname(os.path.abspath(__file__))\n"
                             "for line in open(os.path.join(HERE, 'jobs.yaml')):\n"
                             "    print(app.dispatch(line.split(':', 1)[1].strip()))\n"),
            "probe.py": "import app\nprint(app.dispatch('/v2/export'))\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, files)
            E(tmp)
            E(tmp, "--run", "python probe.py")
            edit(tmp, "app.py", "'/v1/export': lambda: 'v1', ", "")
            _, out = gate(tmp)
            self.assertIn("jobs.yaml:1 (names /v1/export)", out)
            code, rout, _ = E(tmp, "--run", "python scheduler.py")
            self.assertEqual(code, 0, rout)
            code, out = gate(tmp)
            self.assertNotIn("jobs.yaml:1 (names", out.split("STAGE 3")[0])
            self.assertIn("now `404", out)


class Hold(unittest.TestCase):
    def test_a_stale_cache_shows_as_a_changed_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp)
            edit(tmp, "model.py", *CACHE)
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("run 2 `python cli.py refund` changed", out)
            self.assertIn("was `now 7`, now `now 12`", out)

    def test_a_leak_into_a_written_file_shows_even_when_the_output_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp)
            edit(tmp, "model.py", *CACHE)
            _, out = gate(tmp)
            self.assertIn("run 3 `python cli.py backup b.json` changed", out)
            self.assertIn("wrote b.json", out)

    def test_an_intended_difference_with_a_reason_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp, runs=("python cli.py total",))
            edit(tmp, "model.py", "return sum(self.lines)", "return sum(self.lines) * 100")
            note(tmp, "- refunds.py::refund: out: refund is not reachable from any command in this app")
            note(tmp, "- backup.py::backup: out: backup is not reachable from any command in this app")
            _, out = gate(tmp)
            self.assertIn("run 1 `python cli.py total` changed", out)
            note(tmp, "- run 1: intended: the user asked for totals in cents")
            _, out = gate(tmp)
            self.assertNotIn("run 1 `python cli.py total` changed", out)

    def test_intended_on_a_run_that_did_not_change_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp)
            edit(tmp, "model.py", *GOOD_CACHE)
            edit(tmp, "model.py", "class Order:", "_CACHE = {}\n\n\nclass Order:")
            note(tmp, "- run 1: intended: the user asked for this to change")
            _, out = gate(tmp)
            self.assertIn("says run 1 changes on purpose, but it prints what it printed before", out)

    def test_no_change_leaves_stage_two_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp)
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("no product file differs", out)

    def test_a_safe_change_with_every_reader_run_is_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            ready(tmp)
            edit(tmp, "model.py", *GOOD_CACHE)
            edit(tmp, "model.py", "class Order:", "_CACHE = {}\n\n\nclass Order:")
            code, out = gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("EVOLVE-GATE: done(3 runs, 3 unchanged, 0 intended", out)
            self.assertIn("- refunds.py::refund (reads total): run 2", out)
            self.assertIn("[[fill:", out)
            with open(os.path.join(tmp, ".evolve", "state.json"), encoding="utf-8") as fh:
                self.assertEqual(len(json.load(fh)["runs"]), 3)


if __name__ == "__main__":
    unittest.main()
