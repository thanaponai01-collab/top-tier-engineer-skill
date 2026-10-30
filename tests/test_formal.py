#!/usr/bin/env python3
"""
formal.py - the records, the runs, the break and the drift behind formal-check.

Each test plants the thing a stage exists to catch, so disabling that part of the gate turns it red.
The verifier is a stdlib harness that steps the real Counter through every interleaving, so no test
needs Java or TLC. Run them all with `python -m unittest discover tests`.
"""
import hashlib, os, re, subprocess, tempfile, unittest

from _helpers import run, ROOT, SCRIPTS

# Each yield ends one atomic step; the harness only steps a thread waiting to acquire when the lock is free.
COUNTER = (
    "class Counter:\n"                                       # 1
    "    def __init__(self):\n"                              # 2
    "        self.value = 0\n"                               # 3
    "        self.lock_holder = None\n"                      # 4
    "\n"                                                     # 5
    "    def increment(self, me):\n"                         # 6
    "        \"\"\"One increment; each yield ends one atomic step.\"\"\"\n"   # 7
    "        yield \"acquire\"\n"                            # 8
    "        self.lock_holder = me\n"                        # 9
    "        v = self.value\n"                               # 10
    "        yield \"read\"\n"                               # 11
    "        self.value = v + 1\n"                           # 12
    "        self.lock_holder = None\n")                     # 13
CLIENT = (
    "def fetch(get, retries=3):\n"                           # 1
    "    for attempt in range(retries):\n"                   # 2
    "        try:\n"
    "            return get()\n"
    "        except OSError:\n"
    "            if attempt == retries - 1:\n"
    "                raise\n")
HARNESS = (
    "\"\"\"Every interleaving of N increments on app.counter.Counter ends with value N.\"\"\"\n"
    "import os, sys\n"
    "sys.path.insert(0, os.getcwd())\n"
    "from app.counter import Counter\n"
    "\n"
    "def replay(schedule, n):\n"
    "    c = Counter()\n"
    "    gens = [c.increment(i) for i in range(n)]\n"
    "    label = [next(g) for g in gens]\n"
    "    for t in schedule:\n"
    "        try:\n"
    "            label[t] = next(gens[t])\n"
    "        except StopIteration:\n"
    "            label[t] = None\n"
    "    return c, label\n"
    "\n"
    "def enabled(c, label):\n"
    "    return [t for t, l in enumerate(label)\n"
    "            if l is not None and not (l == 'acquire' and c.lock_holder is not None)]\n"
    "\n"
    "def explore(schedule, n):\n"
    "    c, label = replay(schedule, n)\n"
    "    ts = enabled(c, label)\n"
    "    if not ts:\n"
    "        if any(l is not None for l in label):\n"
    "            return schedule, 'deadlock'\n"
    "        return None if c.value == n else (schedule, 'value %d, want %d' % (c.value, n))\n"
    "    for t in ts:\n"
    "        bad = explore(schedule + [t], n)\n"
    "        if bad:\n"
    "            return bad\n"
    "    return None\n"
    "\n"
    "n = int(sys.argv[1]) if len(sys.argv) > 1 else 2\n"
    "bad = explore([], n)\n"
    "if bad:\n"
    "    print('counterexample: threads stepped %s -> %s' % bad)\n"
    "    sys.exit(1)\n"
    "print('ok: every interleaving of %d increments' % n)\n")
BASE = {
    "app/__init__.py": "",
    "app/counter.py": COUNTER,
    "app/client.py": CLIENT,
    "app/util.py": "def add(a, b):\n    return a + b\n",
    "model/check_counter.py": HARNESS,
    "README.md": "# app\n",
}
CMD = "python model/check_counter.py 2"
NO_LOCK = ("app/counter.py", "        self.lock_holder = me\n", "        pass\n")
GIT = ["-c", "user.email=t@t", "-c", "user.name=t"]


def write(tmp, files):
    for rel_path, text in files.items():
        p = os.path.join(tmp, *rel_path.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


def git(tmp, *args):
    return subprocess.run(["git", "-C", tmp, *GIT, *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def commit(tmp, msg):
    git(tmp, "add", "-A")
    git(tmp, "commit", "-qm", msg)
    return git(tmp, "rev-parse", "HEAD")


def edit(tmp, rel_path, old, new):
    p = os.path.join(tmp, *rel_path.split("/"))
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    assert old in text, (rel_path, old)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.replace(old, new))


def read(tmp, rel_path):
    with open(os.path.join(tmp, *rel_path.split("/")), encoding="utf-8") as fh:
        return fh.read()


def counter_check(**over):
    f = {"property": "two increments always add two to the value",
         "harm": "a lost increment undercounts, and nothing reports it",
         "target": "app/counter.py:9",
         "tool": "interleave-harness 1.0",
         "cmd": f"`{CMD}`",
         "model": "model/check_counter.py",
         "map": ["increment -> app/counter.py:6", "lock_holder -> app/counter.py:9",
                 "value -> app/counter.py:12"],
         "covers": "app/counter.py",
         "bounds": "2 threads, one increment each",
         "assumes": "each yield ends one atomic step",
         "break": "app/counter.py",
         "old": "`self.lock_holder = me`",
         "new": "`pass`"}
    f.update(over)
    lines = ["# counter"]
    for k, v in f.items():
        if v is None:
            continue
        for item in (v if isinstance(v, list) else [v]):
            lines.append(f"- {k}: {item}")
    return "\n".join(lines) + "\n"


def check(tmp, text, name="counter"):
    write(tmp, {f".formal/{name}.md": text})


def tree(tmp):
    """{path: sha} of every file outside .git and .formal."""
    out = {}
    for d, subdirs, names in os.walk(tmp):
        subdirs[:] = [s for s in subdirs if s not in (".git", ".formal")]
        for n in names:
            p = os.path.join(d, n)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, tmp)] = hashlib.sha256(fh.read()).hexdigest()
    return out


class Repo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        write(self.tmp, BASE)
        git(self.tmp, "init", "-q")
        self.base = commit(self.tmp, "counter and its harness")

    def tearDown(self):
        self._tmp.cleanup()

    def gate(self, *extra):
        return run("formal.py", self.tmp, "--gate", *extra)

    def synced(self):
        """The counter check, green and locked at the base commit."""
        check(self.tmp, counter_check())
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("counter: in-sync", out)


class Scan(Repo):
    def test_the_lock_and_the_retry_are_candidates_and_plain_code_is_not(self):
        code, out, err = run("formal.py", self.tmp, "--scan")
        self.assertEqual(code, 0, out + err)
        self.assertRegex(out, r"app/counter\.py:(4|9|13)\b")
        self.assertIn("app/client.py:2", out)
        self.assertNotIn("app/util.py", out)
        self.assertNotIn("README.md", out)


class Record(Repo):
    def test_a_missing_field_is_refused(self):
        check(self.tmp, counter_check(harm=None, bounds=None))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("counter: missing `- harm:`", out)
        self.assertIn("counter: missing `- bounds:`", out)


class Map(Repo):
    def test_a_map_line_must_point_at_covered_code_that_exists_and_a_model_element_that_does(self):
        check(self.tmp, counter_check(map=["increment -> app/counter.py:99", "nonesuch -> app/counter.py:9",
                                           "value -> README.md:1"],
                                      covers=["app/counter.py", "app/client.py"]))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("counter: map app/counter.py:99 is past the end of the file", out)
        self.assertIn("counter: map element `nonesuch` is not in model/check_counter.py", out)
        self.assertIn("counter: map README.md:1 points outside covers", out)
        self.assertIn("counter: covers app/client.py has no map line", out)


class Break(Repo):
    def test_a_break_in_the_model_or_with_missing_text_is_refused(self):
        check(self.tmp, counter_check(**{"break": "model/check_counter.py", "old": "`return None`"}))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("counter: the break edits model/check_counter.py, a model file; break the code it covers", out)

        check(self.tmp, counter_check(old="`self.lock_owner = me`"))
        _, out, _ = self.gate()
        self.assertIn("counter: the break's old text is not in app/counter.py", out)

    def test_a_check_that_still_passes_with_the_break_applied_cannot_fail(self):
        check(self.tmp, counter_check(cmd='`python -c "pass"`'))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn('counter: `python -c "pass"` still passes with the break applied: it cannot fail', out)

    def test_a_check_green_on_the_code_and_red_with_the_break_clears(self):
        self.synced()
        _, out, _ = self.gate()
        self.assertIn("FORMAL-GATE: done", out)
        self.assertIn(self.base, read(self.tmp, ".formal/counter.lock"))


class Finding(Repo):
    def test_a_failure_on_the_code_is_a_bug_told_as_steps_not_a_refusal_to_weaken(self):
        edit(self.tmp, *NO_LOCK)
        check(self.tmp, counter_check(**{"break": None, "old": None, "new": None}))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn(f"counter: `{CMD}` fails on the code: a bug needs two or more `- step:` lines", out)

        check(self.tmp, counter_check(**{"break": None, "old": None, "new": None},
                                      step=["thread 0 reads value 0 app/counter.py:10",
                                            "thread 1 reads value 0, the lock never taken app/counter.py:10",
                                            "both write 1, one increment lost app/counter.py:12"]))
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("counter: bug", out)

    def test_a_step_must_cite_a_line_that_exists(self):
        edit(self.tmp, *NO_LOCK)
        check(self.tmp, counter_check(**{"break": None, "old": None, "new": None},
                                      step=["thread 0 reads app/counter.py:10", "thread 1 reads app/counter.py:400"]))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("counter: step app/counter.py:400 is past the end of the file", out)


class Lock(Repo):
    def test_the_property_and_bounds_cannot_change_without_a_changed_line_with_evidence(self):
        self.synced()
        check(self.tmp, counter_check(property="increments mostly add up"))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("counter: the property changed since it was locked", out)

        check(self.tmp, counter_check(bounds="1 thread, one increment"))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("counter: the bounds changed since it was locked", out)

        check(self.tmp, counter_check(bounds="1 thread, one increment",
                                      changed="2 threads, one increment each -> 1 thread, one increment "
                                              "evidence: deadbeef12"))
        _, out, _ = self.gate()
        self.assertIn("counter: evidence deadbeef12 is not a commit or a line in this repo", out)

        check(self.tmp, counter_check(bounds="1 thread, one increment",
                                      changed="2 threads, one increment each -> 1 thread, one increment "
                                              f"evidence: {self.base}"))
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("counter: bounds changed: 2 threads, one increment each -> 1 thread, one increment", out)
        self.assertIn("bounds changed:", read(self.tmp, ".formal/answer.md"))


class Run(Repo):
    def test_a_check_over_the_budget_is_too_slow_to_rerun(self):
        check(self.tmp, counter_check(cmd='`python -c "import time; time.sleep(3)"`'))
        code, out, _ = self.gate("--budget", "1")
        self.assertEqual(code, 1)
        self.assertIn("too slow to rerun", out)

    def test_a_missing_tool_is_blocked(self):
        check(self.tmp, counter_check(cmd="`formal-no-such-verifier model/check_counter.py`"))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("counter: blocked:", out)

    def test_with_ci_the_check_must_run_there(self):
        check(self.tmp, counter_check())
        write(self.tmp, {".github/workflows/ci.yml": "jobs:\n  t:\n    steps:\n      - run: python -m unittest\n"})
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn(f"counter: `{CMD}` is not in the CI config (.github/workflows/ci.yml)", out)
        write(self.tmp, {".github/workflows/ci.yml": f"jobs:\n  t:\n    steps:\n      - run: {CMD}\n"})
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)


class Drift(Repo):
    def test_a_commit_to_covered_code_holds_the_check_stale_until_classified_and_rerun(self):
        self.synced()
        edit(self.tmp, "app/counter.py", "        self.lock_holder = None\n",
             "        self.lock_holder = None\n# counts are per process\n")
        later = commit(self.tmp, "note the scope of the count")
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn(f"counter: stale: 1 commit(s) touched covered code since {self.base[:10]}", out)

        code, out, _ = run("formal.py", self.tmp, "--drift")
        self.assertIn(later[:10], out)
        self.assertIn(later[:10], read(self.tmp, ".formal/counter.drift.md"))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn(f"counter: {later[:10]} has no drift line", out)

        write(self.tmp, {".formal/counter.drift.md": f"- {later[:10]}: no-effect: a comment after the code\n"})
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("counter: updated", out)
        self.assertIn(git(self.tmp, "rev-parse", "HEAD"), read(self.tmp, ".formal/counter.lock"))

    def test_promise_changed_needs_evidence(self):
        self.synced()
        edit(self.tmp, "app/counter.py", "        self.lock_holder = None\n",
             "        self.lock_holder = None\n# counts are per process\n")
        later = commit(self.tmp, "note the scope of the count")
        write(self.tmp, {".formal/counter.drift.md": f"- {later[:10]}: promise-changed: counts are per process now\n"})
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn(f"counter: {later[:10]} is promise-changed with no evidence", out)

    def test_a_renamed_covered_file_is_still_followed(self):
        self.synced()
        git(self.tmp, "mv", "app/counter.py", "app/tally.py")
        commit(self.tmp, "rename the counter module")
        edit(self.tmp, "app/tally.py", "        self.value = v + 1\n", "        self.value = v + 2\n")
        later = commit(self.tmp, "count by two")
        code, out, _ = run("formal.py", self.tmp, "--drift")
        self.assertIn("app/counter.py -> app/tally.py", out)
        self.assertIn(later[:10], out)       # an edit after the rename is still covered code
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("counter: stale:", out)


class Answer(Repo):
    def test_the_reply_is_checked_against_what_the_gate_recorded(self):
        self.synced()
        answer = os.path.join(self.tmp, ".formal", "answer.md")
        draft = read(self.tmp, ".formal/answer.md")
        self.assertIn("## counter", draft)
        self.assertIn("Outcome: in-sync", draft)

        code, out, _ = run("formal.py", self.tmp, "--answer-check", answer)
        self.assertEqual(code, 1)
        self.assertIn("unfilled [[fill", out)
        filled = re.sub(r"\[\[fill:[^\]]*\]\]", "checked every interleaving of two increments", draft)
        write(self.tmp, {".formal/answer.md": filled})
        code, out, _ = run("formal.py", self.tmp, "--answer-check", answer)
        self.assertEqual(code, 0, out)
        self.assertIn("ANSWER OK", out)

        edit(self.tmp, "app/counter.py", "        self.lock_holder = None\n",
             "        self.lock_holder = None\n# counts are per process\n")
        commit(self.tmp, "note the scope of the count")
        self.gate()
        write(self.tmp, {".formal/answer.md": filled + "\n## ghost\nOutcome: in-sync\n"})
        code, out, _ = run("formal.py", self.tmp, "--answer-check", answer)
        self.assertEqual(code, 1)
        self.assertIn("calls counter in-sync, but the gate recorded it stale", out)
        self.assertIn("names ghost, a check the gate did not record", out)


class Untouched(Repo):
    def test_the_repo_is_byte_identical_after_a_full_run_apart_from_formal(self):
        check(self.tmp, counter_check())
        before = tree(self.tmp)
        run("formal.py", self.tmp, "--scan")
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)
        run("formal.py", self.tmp, "--drift")
        self.assertEqual(tree(self.tmp), before)


class OneRefusal(Repo):
    def test_one_refusal_names_every_gap_at_once(self):
        check(self.tmp, counter_check(harm=None, map=["increment -> app/counter.py:99", "value -> app/counter.py:12"],
                                      **{"break": "model/check_counter.py", "old": "`return None`"}))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("missing `- harm:`", out)                  # stage 1
        self.assertIn("is past the end of the file", out)        # stage 2
        self.assertIn("a model file; break the code", out)       # stage 4
        self.assertIn("FORMAL-GATE: open(1, 2, 4)", out)


class Shape(unittest.TestCase):
    def test_skill_body_is_short_and_shaped_like_its_siblings(self):
        with open(os.path.join(ROOT, "plugin", "skills", "formal-check", "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        body = text.split("---", 2)[2]
        self.assertLessEqual(len(body), 5000)
        self.assertIn("disable-model-invocation: true", text)
        for part in ("**Goal:**", "`F` is `python", "| Stage | Holds when |"):
            self.assertIn(part, body)

    def test_other_helpers_skip_formal_and_formal_skips_theirs(self):
        for tool in ("debug.py", "structure-report.py", "verify.py", "threat.py", "evolve.py", "perf.py",
                     "release.py", "wire.py", "features.py", "graph-audit.py", "blast.py", "mistake.py"):
            with open(os.path.join(SCRIPTS[tool], tool), encoding="utf-8") as fh:
                self.assertTrue('".formal"' in fh.read(), f"{tool} does not skip .formal/")
        with open(os.path.join(SCRIPTS["formal.py"], "formal.py"), encoding="utf-8") as fh:
            src = fh.read()
        for state in (".verify-state", ".wire", ".features", ".release", ".evolve", ".perf", ".blast", ".mistakes"):
            self.assertIn(f'"{state}"', src, f"formal.py does not skip {state}/")


if __name__ == "__main__":
    unittest.main()
