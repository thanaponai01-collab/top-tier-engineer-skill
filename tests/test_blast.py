#!/usr/bin/env python3
"""
blast.py - the consumer list, the verdicts and the safety fact behind blast-radius.

Each test plants the thing a stage exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import hashlib, json, os, re, subprocess, tempfile, unittest

from _helpers import run, ROOT, SCRIPTS

APP = {
    "shop/__init__.py": "",
    "shop/orders.py": (
        "def make_order(sku, qty):\n"
        "    return {\"sku\": sku, \"qty\": qty}\n"),
    "shop/report.py": (
        "from shop.orders import make_order\n\n\n"
        "def line(sku):\n"
        "    o = make_order(sku, 1)\n"
        "    return o[\"sku\"]\n"),
    # a caller several imports away: through a module alias, no name of the function imported
    "shop/checkout.py": (
        "from shop import orders as o\n\n\n"
        "def buy(sku):\n"
        "    return o.make_order(sku, 2)\n"),
    "shop/ship.py": (
        "def label(order):\n"
        "    return f\"{order['sku']} x{order['qty']}\"\n"),
    "dash/app.js": "export function show(order) {\n  return order.sku + ': ' + order.qty;\n}\n",
    "README.md": "# shop\n",
    # another helper's state: never a consumer
    ".wire/notes.py": "x = make_order('a', 1)['qty']\n",
}
SIGNATURE = ("shop/orders.py", "def make_order(sku, qty):", "def make_order(sku, qty, price=0):")
RENAME = ("shop/orders.py", "\"qty\": qty", "\"quantity\": qty")
PROOF = 'python -c "from shop.report import line; from shop.checkout import buy; line(\'w\'); buy(\'w\')"'
FACT = (
    "- fact: make_order's new price parameter has a default, so every old call with two arguments still works\n"
    "- cite: shop/orders.py:1\n"
    f"- proof: `{PROOF}`\n"
    "- break: shop/orders.py\n"
    "- old: `price=0`\n"
    "- new: `price`\n")


def write(tmp, files):
    for rel_path, text in files.items():
        p = os.path.join(tmp, *rel_path.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


def git(tmp, *args):
    return subprocess.run(["git", "-C", tmp, *args], capture_output=True, text=True, check=True)


def make(tmp):
    write(tmp, APP)
    git(tmp, "init", "-q")
    git(tmp, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    git(tmp, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")


def edit(tmp, rel_path, old, new):
    p = os.path.join(tmp, *rel_path.split("/"))
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    assert old in text, (rel_path, old)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.replace(old, new))


def consumers(tmp):
    with open(os.path.join(tmp, ".blast", "consumers.json"), encoding="utf-8") as fh:
        return {c["site"]: c for c in json.load(fh)["consumers"]}


def fill(tmp, lines):
    p = os.path.join(tmp, ".blast", "verdicts.md")
    with open(p, encoding="utf-8") as fh:
        keep = [ln for ln in fh.read().splitlines() if "[[fill" not in ln]
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(keep + lines) + "\n")


def tree(tmp):
    """{path: sha} of every file outside .git and .blast."""
    out = {}
    for d, subdirs, names in os.walk(tmp):
        subdirs[:] = [s for s in subdirs if s not in (".git", ".blast")]
        for n in names:
            p = os.path.join(d, n)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, tmp)] = hashlib.sha256(fh.read()).hexdigest()
    return out


CLEARED = ["- shop/report.py:5: cleared: two arguments, and price has a default at shop/orders.py:1",
           "- shop/checkout.py:5: cleared: two arguments, and price has a default at shop/orders.py:1"]


class List(unittest.TestCase):
    def test_a_changed_signature_is_listed_with_callers_in_other_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            edit(tmp, *SIGNATURE)
            code, out, err = run("blast.py", tmp, "--base", "HEAD")
            self.assertEqual(code, 0, out + err)
            found = consumers(tmp)
            self.assertIn("shop/report.py:5", found)      # make_order(sku, 1)
            self.assertIn("shop/checkout.py:5", found)    # o.make_order(sku, 2), through an alias
            self.assertNotIn("shop/orders.py:1", found)   # the change itself is not its own consumer
            self.assertIn("make_order", out)

    def test_a_renamed_key_is_listed_with_string_readers_in_untouched_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            edit(tmp, *RENAME)
            run("blast.py", tmp, "--base", "HEAD")
            found = consumers(tmp)
            self.assertIn("shop/ship.py:2", found)        # order['qty'] in Python
            self.assertIn("dash/app.js:2", found)         # order.qty in a file no AST reads
            self.assertIn("`qty`", " ".join(found["dash/app.js:2"]["what"]))
            self.assertFalse(any(s.startswith(".wire/") for s in found), found)   # other helpers' state


class Gate(unittest.TestCase):
    def test_every_consumer_needs_a_verdict_and_breaks_or_cleared_cite_a_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            edit(tmp, *SIGNATURE)
            run("blast.py", tmp, "--base", "HEAD")
            code, out, _ = run("blast.py", tmp, "--gate")
            self.assertEqual(code, 1)
            self.assertIn("2 consumer(s) have no verdict", out)
            with open(os.path.join(tmp, ".blast", "verdicts.md"), encoding="utf-8") as fh:
                slots = fh.read()
            self.assertIn("- shop/report.py:5: [[fill:", slots)
            self.assertIn("- shop/checkout.py:5: [[fill:", slots)
            fill(tmp, ["- shop/report.py:5: cleared: it passes two arguments, which still works",
                       "- shop/checkout.py:5: breaks: it passes two arguments, see shop/orders.py:99"])
            code, out, _ = run("blast.py", tmp, "--gate")
            self.assertEqual(code, 1)
            self.assertIn("shop/report.py:5: `cleared` needs the file:line or library source it rests on", out)
            self.assertIn("shop/checkout.py:5: cites shop/orders.py:99, past the end of the file", out)
            fill(tmp, CLEARED)
            _, out, _ = run("blast.py", tmp, "--gate")
            self.assertIn("STAGE 2 account: every consumer has a verdict: holds", out)

    def test_the_list_must_be_current_with_the_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            edit(tmp, *SIGNATURE)
            run("blast.py", tmp, "--base", "HEAD")
            edit(tmp, *RENAME)
            code, out, _ = run("blast.py", tmp, "--gate")
            self.assertEqual(code, 1)
            self.assertIn("the code changed since the list (shop/orders.py)", out)


class Fact(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = self._tmp.name
        make(self.tmp)
        edit(self.tmp, *SIGNATURE)
        run("blast.py", self.tmp, "--base", "HEAD")
        run("blast.py", self.tmp, "--gate")
        fill(self.tmp, CLEARED)

    def tearDown(self):
        self._tmp.cleanup()

    def state(self):
        with open(os.path.join(self.tmp, ".blast", "state.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def test_a_proof_that_passes_with_the_break_is_refused(self):
        write(self.tmp, {".blast/fact.md": FACT.replace(f"`{PROOF}`", '`python -c "print(1)"`')})
        code, out, _ = run("blast.py", self.tmp, "--gate")
        self.assertEqual(code, 1)
        self.assertIn("passes with the break applied: it cannot fail", out)
        self.assertLess(self.state()["level"], 4)

    def test_a_proof_red_on_the_break_and_green_on_the_change_is_level_4(self):
        write(self.tmp, {".blast/fact.md": FACT})
        code, out, _ = run("blast.py", self.tmp, "--gate")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.state()["level"], 4)
        self.assertIn("Level: 4", out)
        self.assertIn("BLAST-GATE: done(", out)

    def test_below_level_4_the_draft_says_unproven(self):
        write(self.tmp, {".blast/fact.md": FACT.split("- proof:")[0]})
        code, out, _ = run("blast.py", self.tmp, "--gate")
        self.assertEqual(code, 1)
        self.assertEqual(self.state()["level"], 2)   # said so, with a line that exists
        self.assertIn("Level: 2 (unproven)", out)
        self.assertNotRegex(out.split("ANSWER")[1], r"(?i)(?<!not )\bsafe\b")

    def test_the_answer_is_checked_against_the_recorded_level(self):
        write(self.tmp, {".blast/fact.md": FACT.split("- proof:")[0]})
        run("blast.py", self.tmp, "--gate")
        answer = os.path.join(self.tmp, ".blast", "answer.md")   # the draft, filled in place
        with open(answer, encoding="utf-8") as fh:
            draft = fh.read()
        write(self.tmp, {".blast/answer.md": re.sub(r"Level: .*", "Level: 4 (ran it)", draft)
                         .replace("Verdict: unproven", "Verdict: safe")})
        code, out, _ = run("blast.py", self.tmp, "--answer-check", answer)
        self.assertEqual(code, 1)
        self.assertIn("states level 4, but the helper recorded 2", out)
        self.assertIn("says safe at level 2", out)

        write(self.tmp, {".blast/fact.md": FACT})
        run("blast.py", self.tmp, "--gate")
        with open(answer, encoding="utf-8") as fh:
            draft = fh.read()
        code, out, _ = run("blast.py", self.tmp, "--answer-check", answer)
        self.assertEqual(code, 1)
        self.assertIn("unfilled [[fill", out)
        write(self.tmp, {".blast/answer.md": re.sub(r"\[\[fill:[^\]]*\]\]", "adds an optional price to make_order",
                                             draft)})
        code, out, _ = run("blast.py", self.tmp, "--answer-check", answer)
        self.assertEqual(code, 0, out)
        self.assertIn("ANSWER OK", out)


class Untouched(unittest.TestCase):
    def test_the_repo_is_byte_identical_after_a_full_run_apart_from_blast(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            edit(tmp, *SIGNATURE)
            before = tree(tmp)
            run("blast.py", tmp, "--base", "HEAD")
            run("blast.py", tmp, "--gate")
            fill(tmp, CLEARED)
            write(tmp, {".blast/fact.md": FACT})
            code, out, _ = run("blast.py", tmp, "--gate", "--app", PROOF)
            self.assertEqual(code, 0, out)
            self.assertIn("Level: 5", out)
            self.assertEqual(tree(tmp), before)


class OneRefusal(unittest.TestCase):
    def test_one_refusal_names_every_gap_at_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            edit(tmp, *SIGNATURE)
            run("blast.py", tmp, "--base", "HEAD")
            run("blast.py", tmp, "--gate")
            fill(tmp, ["- shop/report.py:5: cleared: it passes two arguments, which still works"])
            write(tmp, {".blast/fact.md": FACT.replace("`price=0`", "`price=1`")})
            code, out, _ = run("blast.py", tmp, "--gate")
            self.assertEqual(code, 1)
            self.assertIn("1 consumer(s) have no verdict", out)                      # checkout
            self.assertIn("shop/report.py:5: `cleared` needs the file:line", out)    # no cite
            self.assertIn("the break's old text `price=1` is not in shop/orders.py", out)
            self.assertIn("BLAST-GATE: open(2, 3)", out)


class Shape(unittest.TestCase):
    def test_skill_body_is_short_and_shaped_like_its_siblings(self):
        with open(os.path.join(ROOT, "plugin", "skills", "blast-radius", "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        body = text.split("---", 2)[2]
        self.assertLessEqual(len(body), 5000)
        self.assertIn("disable-model-invocation: true", text)
        for part in ("**Goal:**", "`B` is `python", "| Stage | Holds when |"):
            self.assertIn(part, body)

    def test_other_helpers_skip_blast_and_blast_skips_theirs(self):
        for tool in ("debug.py", "structure-report.py", "verify.py", "threat.py", "evolve.py", "perf.py",
                     "release.py", "wire.py", "features.py", "graph-audit.py"):
            with open(os.path.join(SCRIPTS[tool], tool), encoding="utf-8") as fh:
                self.assertIn('".blast"', fh.read(), f"{tool} does not skip .blast/")
        with open(os.path.join(SCRIPTS["blast.py"], "blast.py"), encoding="utf-8") as fh:
            src = fh.read()
        for state in (".verify-state", ".wire", ".features", ".release", ".evolve", ".perf"):
            self.assertIn(f'"{state}"', src, f"blast.py does not skip {state}/")


if __name__ == "__main__":
    unittest.main()
