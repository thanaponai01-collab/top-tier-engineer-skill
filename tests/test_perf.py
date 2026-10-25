#!/usr/bin/env python3
"""
perf.py - the measure, change and guard stages behind perf-optimize.

Each test plants the thing a guard exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import json, os, tempfile, unittest

from _helpers import run

APP = {
    "app.py": ("import sys\nimport time\n\nimport fmt\n\n\ndef work(n):\n    time.sleep(0.3)\n"
               "    return sum(range(n))\n\n\ndef main():\n    print(fmt.show(work(int(sys.argv[1]))))\n\n\n"
               "if __name__ == '__main__':\n    main()\n"),
    "fmt.py": "def show(x):\n    return f'total {x}'\n",
    "tests/test_app.py": ("import unittest\nimport app\n\n\nclass T(unittest.TestCase):\n"
                          "    def test_sum(self):\n        self.assertEqual(app.work(4), 6)\n"),
}
GUARD = ("import time\nimport unittest\nimport app\n\n\nclass Speed(unittest.TestCase):\n"
         "    def test_work_is_quick(self):\n        start = time.perf_counter()\n        app.work(10)\n"
         "        self.assertLess(time.perf_counter() - start, 0.15)\n")
SLEEP = ("    time.sleep(0.3)\n", "")
GUARD_CMD = "python -m unittest tests.test_speed"


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


def measure(tmp, size, *extra):
    return run("perf.py", tmp, "--measure", f"python app.py {size}", "--size", str(size), "--runs", "2", *extra)


def gate(tmp, *extra):
    return run("perf.py", tmp, "--gate", *extra)


def ledger(tmp):
    with open(os.path.join(tmp, ".perf", "state.json"), encoding="utf-8") as fh:
        return json.load(fh)


class Measure(unittest.TestCase):
    def test_size_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, _ = run("perf.py", tmp, "--measure", "python app.py 10")
            self.assertNotEqual(code, 0)
            self.assertIn("--size", out)

    def test_records_time_profile_and_keeps_the_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, _ = measure(tmp, 10)
            self.assertEqual(code, 0, out)
            w = ledger(tmp)["workloads"][0]
            self.assertGreater(min(w["before"]["times"]), 0.3)
            self.assertIn("app.py::work", [r["func"] for r in w["profile"]["mine"]])
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".perf", "before", "app.py")))

    def test_refuses_output_that_moves(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            edit(tmp, "fmt.py", "return f'total {x}'", "import time; return f'total {x} {time.time()}'")
            code, out, _ = measure(tmp, 10)
            self.assertNotEqual(code, 0)
            self.assertIn("printed something different", out)

    def test_refuses_a_failing_workload(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, _ = run("perf.py", tmp, "--measure", "python app.py", "--size", "1", "--runs", "1")
            self.assertNotEqual(code, 0)
            self.assertIn("exited", out)

    def test_a_late_measure_times_the_code_as_it_was(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            edit(tmp, "app.py", *SLEEP)
            measure(tmp, 1000)
            late = [w for w in ledger(tmp)["workloads"] if w["size"] == "1000"][0]
            self.assertGreater(min(late["before"]["times"]), 0.3)


class Stages(unittest.TestCase):
    def test_one_size_leaves_stage_one_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            code, out, _ = gate(tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("STAGE 1 measure", out)
            self.assertIn("one size measured", out)

    def test_nothing_measured_is_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out, _ = gate(tmp)
            self.assertIn("nothing measured", out)
            self.assertNotEqual(code, 0)

    def test_diagnosis_only_is_done_with_growth(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            measure(tmp, 1000)
            code, out, _ = gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("PERF-GATE: done", out)
            self.assertIn("From size 10 to 1000", out)
            self.assertIn("Diagnosis only", out)

    def test_changed_output_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            measure(tmp, 1000)
            edit(tmp, "app.py", *SLEEP)
            edit(tmp, "app.py", "return sum(range(n))", "return sum(range(n)) + 1")
            code, out, _ = gate(tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("prints something different now", out)

    def test_a_change_inside_the_noise_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            measure(tmp, 1000)
            edit(tmp, "app.py", "    return sum(range(n))\n", "    total = sum(range(n))\n    return total\n")
            code, out, _ = gate(tmp, "--guard", GUARD_CMD)
            self.assertNotEqual(code, 0)
            self.assertIn("not faster beyond the noise", out)
            self.assertIn("runs alternated", out)

    def test_a_change_no_profile_aimed_at_is_refused_until_explained(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            measure(tmp, 1000)
            edit(tmp, "app.py", *SLEEP)
            edit(tmp, "fmt.py", "return f'total {x}'", "return 'total ' + str(x)")
            make(tmp, {"tests/test_speed.py": GUARD})
            code, out, _ = gate(tmp, "--guard", GUARD_CMD)
            self.assertIn("fmt.py::show changed, but no profile gave it", out)
            self.assertNotEqual(code, 0)
            make(tmp, {".perf/notes.md": "- fmt.py::show: it is a spelling change, kept on purpose\n"})
            code, out, _ = gate(tmp)
            self.assertNotIn("fmt.py::show changed", out)

    def test_no_guard_leaves_stage_three_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            measure(tmp, 1000)
            edit(tmp, "app.py", *SLEEP)
            code, out, _ = gate(tmp)
            self.assertNotEqual(code, 0)
            self.assertIn("STAGE 2 change: same output", out)
            self.assertIn("no guard", out)

    def test_a_guard_blind_to_the_slow_code_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            measure(tmp, 1000)
            edit(tmp, "app.py", *SLEEP)
            code, out, _ = gate(tmp, "--guard", "python -m unittest tests.test_app")
            self.assertNotEqual(code, 0)
            self.assertIn("with only app.py put back as it was, the guard still passes", out)

    def test_a_guard_that_runs_no_tests_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            measure(tmp, 1000)
            edit(tmp, "app.py", *SLEEP)
            make(tmp, {"tests/test_none.py": "import unittest\n"})
            code, out, _ = gate(tmp, "--guard", "python -m unittest tests.test_none")
            self.assertNotEqual(code, 0)
            self.assertIn("does not pass on the tree now (no tests", out)

    def test_measured_aimed_and_guarded_is_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            measure(tmp, 1000)
            edit(tmp, "app.py", *SLEEP)
            make(tmp, {"tests/test_speed.py": GUARD})
            code, out, _ = gate(tmp, "--guard", GUARD_CMD)
            self.assertEqual(code, 0, out)
            self.assertIn("PERF-GATE: done(2 workloads, changed 1 files)", out)
            self.assertIn("output identical", out)
            self.assertNotIn("alternated", out)   # far past the noise: the old code is not run again
            self.assertIn("Changed: app.py::work", out)
            code, out, _ = gate(tmp)   # the guard is remembered
            self.assertEqual(code, 0, out)

    def test_tests_are_not_counted_as_the_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            measure(tmp, 10)
            measure(tmp, 1000)
            edit(tmp, "tests/test_app.py", "app.work(4), 6", "app.work(5), 10")
            code, out, _ = gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("Diagnosis only", out)


if __name__ == "__main__":
    unittest.main()
