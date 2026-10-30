#!/usr/bin/env python3
"""
mistake.py - the classes, the proofs and the rule table behind mistake-proof.

Each test plants the thing a stage exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import datetime, hashlib, json, os, re, subprocess, tempfile, unittest

from _helpers import run, ROOT, SCRIPTS

TODAY = datetime.date.today().isoformat()
BASE = {
    "app/__init__.py": "",
    "app/core.py": "def total(xs):\n    return sum(xs)\n",
    "README.md": "# app\n",
}
DEBUG = ("app/core.py", "    return sum(xs)\n", "    print(\"debug\", xs)\n    return sum(xs)\n")
# The check the agent writes: fails while any file under app/ calls print(.
NO_PRINT = (
    "import pathlib, sys\n"
    "bad = [f\"{p}:{i}\" for p in sorted(pathlib.Path('app').rglob('*.py'))\n"
    "       for i, ln in enumerate(p.read_text().splitlines(), 1) if 'print(' in ln]\n"
    "print('\\n'.join(f'{b}: use app.log.debug, not print' for b in bad))\n"
    "sys.exit(1 if bad else 0)\n")
CHECK = "python checks/no_print.py"
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


def make(tmp):
    """A history where the same mistake (a debug print) lands, is reverted, and lands again."""
    write(tmp, BASE)
    git(tmp, "init", "-q")
    shas = {"base": commit(tmp, "base")}
    edit(tmp, *DEBUG)
    shas["first"] = commit(tmp, "show totals while debugging")
    git(tmp, "revert", "--no-edit", shas["first"])
    shas["revert"] = git(tmp, "rev-parse", "HEAD")
    edit(tmp, *DEBUG)
    shas["again"] = commit(tmp, "trace totals")
    edit(tmp, DEBUG[0], DEBUG[2], DEBUG[1])
    shas["fix"] = commit(tmp, "drop the trace")
    return shas


def debug_class(shas, **over):
    f = {"evidence": [shas["first"], shas["again"]], "level": "3",
         "why not 1": "print is a builtin; no module boundary can hide it",
         "why not 2": "Python types cannot forbid a builtin call",
         "check": f"`{CHECK}`", "mistake": shas["again"], "check-files": "checks/no_print.py"}
    f.update(over)
    lines = ["## debug-print"]
    for k, v in f.items():
        if v is None:
            continue
        for item in (v if isinstance(v, list) else [v]):
            lines.append(f"- {k}: {item}")
    return "\n".join(lines) + "\n"


def classes(tmp, *blocks):
    write(tmp, {".mistakes/classes.md": "# Mistake classes\n\n" + "\n".join(blocks)})


def rules(tmp, *rows, file="CLAUDE.md"):
    write(tmp, {file: "# Agent rules\n\n<!-- mistake-rules -->\n| Class | Rule | Level | Enforcer | Added |\n"
                      "|---|---|---|---|---|\n" + "".join(r + "\n" for r in rows) + "<!-- /mistake-rules -->\n"})


DEBUG_ROW = f"| debug-print | log with app.log.debug, never print | 3 | checks/no_print.py | {TODAY} |"


def tree(tmp):
    """{path: sha} of every file outside .git and .mistakes."""
    out = {}
    for d, subdirs, names in os.walk(tmp):
        subdirs[:] = [s for s in subdirs if s not in (".git", ".mistakes")]
        for n in names:
            p = os.path.join(d, n)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, tmp)] = hashlib.sha256(fh.read()).hexdigest()
    return out


class Repo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        self.shas = make(self.tmp)

    def tearDown(self):
        self._tmp.cleanup()

    def gate(self):
        return run("mistake.py", self.tmp, "--gate")

    def enforced(self):
        """The debug-print class, its check and its rule row, all as they should be."""
        write(self.tmp, {"checks/no_print.py": NO_PRINT})
        classes(self.tmp, debug_class(self.shas))
        rules(self.tmp, DEBUG_ROW)


class Mine(Repo):
    def test_a_revert_and_the_commit_that_redoes_it_are_both_candidates(self):
        code, out, err = run("mistake.py", self.tmp, "--mine")
        self.assertEqual(code, 0, out + err)
        with open(os.path.join(self.tmp, ".mistakes", "candidates.md"), encoding="utf-8") as fh:
            found = fh.read()
        self.assertIn(self.shas["revert"][:10], found)   # the revert
        self.assertIn(self.shas["first"][:10], found)    # the commit it reverted
        self.assertIn(self.shas["again"][:10], found)    # the later commit that brings it back
        self.assertRegex(found, r"redo.*" + self.shas["again"][:10])
        self.assertTrue(os.path.exists(os.path.join(self.tmp, ".mistakes", "classes.md")))

    def test_add_records_a_correction_with_its_date(self):
        code, out, _ = run("mistake.py", self.tmp, "--add", "used print again instead of app.log")
        self.assertEqual(code, 0, out)
        self.assertIn("added:1", out)
        with open(os.path.join(self.tmp, ".mistakes", "added.md"), encoding="utf-8") as fh:
            self.assertIn(f"- 1 {TODAY}: used print again instead of app.log", fh.read())


class Classes(Repo):
    def test_one_piece_of_evidence_a_missing_one_or_a_missing_why_not_is_refused(self):
        write(self.tmp, {"checks/no_print.py": NO_PRINT})
        rules(self.tmp, DEBUG_ROW)
        classes(self.tmp, debug_class(self.shas, evidence=[self.shas["first"]]))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("debug-print: 1 piece(s) of evidence; a class needs 2", out)

        classes(self.tmp, debug_class(self.shas, evidence=["deadbeef12", "app/core.py:99"]))
        _, out, _ = self.gate()
        self.assertIn("debug-print: evidence deadbeef12 is not a commit in this repo", out)
        self.assertIn("debug-print: evidence app/core.py:99 is past the end of the file", out)

        classes(self.tmp, debug_class(self.shas, **{"why not 1": None, "why not 2": None}))
        _, out, _ = self.gate()
        self.assertIn("debug-print: level 3 needs `- why not 1:`", out)
        self.assertIn("debug-print: level 3 needs `- why not 2:`", out)


class Proof(Repo):
    def test_a_check_that_passes_on_the_past_mistake_is_refused(self):
        write(self.tmp, {"checks/no_print.py": NO_PRINT})
        rules(self.tmp, DEBUG_ROW)
        classes(self.tmp, debug_class(self.shas, check='`python -c "print(1)"`'))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("passes on " + self.shas["again"][:10] + ", where the mistake is: it cannot fail", out)

    def test_a_check_red_on_the_mistake_and_green_now_clears_the_class(self):
        self.enforced()
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("debug-print: enforced (level 3)", out)
        self.assertIn("MISTAKE-GATE: done(", out)
        with open(os.path.join(self.tmp, ".mistakes", "state.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["classes"]["debug-print"]["status"], "enforced")

    def test_a_check_that_fails_now_on_old_uses_gets_the_added_lines_hint(self):
        self.enforced()
        write(self.tmp, {"app/old.py": "def show(x):\n    print(x)\n"})
        commit(self.tmp, "an old use nobody removed")
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn(f"`{CHECK}` fails on the working tree", out)
        self.assertIn("fail only on lines a change adds", out)

    def test_with_ci_the_check_must_run_there(self):
        self.enforced()
        write(self.tmp, {".github/workflows/ci.yml": "jobs:\n  t:\n    steps:\n      - run: python -m unittest\n"})
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn(f"`{CHECK}` is not in the CI config (.github/workflows/ci.yml)", out)
        write(self.tmp, {".github/workflows/ci.yml": f"jobs:\n  t:\n    steps:\n      - run: {CHECK}\n"})
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)


class Rules(Repo):
    def test_a_missing_enforcer_is_refused_and_an_unenforced_rule_that_recurred_is_a_repeat(self):
        write(self.tmp, {"checks/no_print.py": NO_PRINT})
        naming = ("## naming\n"
                  f"- evidence: {self.shas['first']}\n- evidence: {self.shas['again']}\n- level: 5\n"
                  "- why not 1: a judgment call\n- why not 2: a judgment call\n"
                  "- why not 3: a judgment call\n- why not 4: a judgment call\n")
        classes(self.tmp, debug_class(self.shas), naming)
        rules(self.tmp, DEBUG_ROW.replace("checks/no_print.py", "checks/missing.py"),
              "| naming | name totals after what they sum | 5 | none | 2000-01-01 |")
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("debug-print: the enforcer checks/missing.py does not exist", out)
        self.assertIn("naming: repeat:", out)
        self.assertIn("after its rule was added on 2000-01-01, and nothing enforces it", out)

    def test_a_class_with_no_row_is_refused_with_the_row_drafted(self):
        write(self.tmp, {"checks/no_print.py": NO_PRINT})
        classes(self.tmp, debug_class(self.shas))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("no rule table", out)
        self.assertIn("| debug-print |", out)

    def test_an_exception_needs_a_human_and_a_date_still_to_come(self):
        self.enforced()
        commit(self.tmp, "the check")
        edit(self.tmp, "app/core.py", "def total", "X = 1  # mistake-ok: debug-print reason=legacy "
                                                   "expires=2999-01-01\n\n\ndef total")
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("app/core.py:1: the exception has no approved=", out)
        edit(self.tmp, "app/core.py", "expires=2999-01-01", "expires=2000-01-01 approved=Pat")
        _, out, _ = self.gate()
        self.assertIn("app/core.py:1: the exception expired on 2000-01-01", out)


class Answer(Repo):
    def test_the_reply_is_checked_against_what_the_gate_recorded(self):
        write(self.tmp, {"checks/no_print.py": NO_PRINT})
        run("mistake.py", self.tmp, "--add", "named a sum `x`")
        run("mistake.py", self.tmp, "--add", "named a sum `tmp`")
        naming = ("## naming\n- evidence: added:1\n- evidence: added:2\n- level: 5\n"
                  "- why not 1: a judgment call\n- why not 2: a judgment call\n"
                  "- why not 3: a judgment call\n- why not 4: a judgment call\n")
        classes(self.tmp, debug_class(self.shas), naming)
        rules(self.tmp, DEBUG_ROW, f"| naming | name totals after what they sum | 5 | none | {TODAY} |")
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("naming: unenforced (level 5", out)
        answer = os.path.join(self.tmp, ".mistakes", "answer.md")
        with open(answer, encoding="utf-8") as fh:
            draft = fh.read()

        lied = re.sub(r"(## naming\n(?:.*\n)*?)Status: unenforced", r"\1Status: enforced", draft)
        lied += "\n## ghost\nStatus: enforced\n"
        write(self.tmp, {".mistakes/answer.md": re.sub(r"\[\[fill:[^\]]*\]\]", "done", lied)})
        code, out, _ = run("mistake.py", self.tmp, "--answer-check", answer)
        self.assertEqual(code, 1)
        self.assertIn("calls naming enforced, but the gate recorded it unenforced", out)
        self.assertIn("names ghost, a class the gate did not clear", out)

        write(self.tmp, {".mistakes/answer.md": draft})
        code, out, _ = run("mistake.py", self.tmp, "--answer-check", answer)
        self.assertEqual(code, 1)
        self.assertIn("unfilled [[fill", out)
        write(self.tmp, {".mistakes/answer.md": re.sub(r"\[\[fill:[^\]]*\]\]", "added checks/no_print.py", draft)})
        code, out, _ = run("mistake.py", self.tmp, "--answer-check", answer)
        self.assertEqual(code, 0, out)
        self.assertIn("ANSWER OK", out)


class Untouched(Repo):
    def test_the_repo_is_byte_identical_after_a_full_run_apart_from_mistakes(self):
        self.enforced()
        before = tree(self.tmp)
        run("mistake.py", self.tmp, "--mine")
        run("mistake.py", self.tmp, "--add", "print again")
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)
        self.assertEqual(tree(self.tmp), before)


class OneRefusal(Repo):
    def test_one_refusal_names_every_gap_at_once(self):
        classes(self.tmp, debug_class(self.shas, evidence=[self.shas["first"]], **{"why not 2": None},
                                      check='`python -c "print(1)"`'))
        rules(self.tmp, DEBUG_ROW.replace("checks/no_print.py", "checks/missing.py"))
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("1 piece(s) of evidence", out)        # stage 1
        self.assertIn("needs `- why not 2:`", out)          # stage 2
        self.assertIn("it cannot fail", out)                # stage 3
        self.assertIn("checks/missing.py does not exist", out)   # stage 4
        self.assertIn("MISTAKE-GATE: open(1, 2, 3, 4)", out)


class Shape(unittest.TestCase):
    def test_skill_body_is_short_and_shaped_like_its_siblings(self):
        with open(os.path.join(ROOT, "plugin", "skills", "mistake-proof", "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        body = text.split("---", 2)[2]
        self.assertLessEqual(len(body), 5000)
        self.assertIn("disable-model-invocation: true", text)
        for part in ("**Goal:**", "`M` is `python", "| Stage | Holds when |"):
            self.assertIn(part, body)

    def test_other_helpers_skip_mistakes_and_mistake_skips_theirs(self):
        for tool in ("debug.py", "structure-report.py", "verify.py", "threat.py", "evolve.py", "perf.py",
                     "release.py", "wire.py", "features.py", "graph-audit.py", "blast.py"):
            with open(os.path.join(SCRIPTS[tool], tool), encoding="utf-8") as fh:
                self.assertIn('".mistakes"', fh.read(), f"{tool} does not skip .mistakes/")
        with open(os.path.join(SCRIPTS["mistake.py"], "mistake.py"), encoding="utf-8") as fh:
            src = fh.read()
        for state in (".verify-state", ".wire", ".features", ".release", ".evolve", ".perf", ".blast"):
            self.assertIn(f'"{state}"', src, f"mistake.py does not skip {state}/")


if __name__ == "__main__":
    unittest.main()
