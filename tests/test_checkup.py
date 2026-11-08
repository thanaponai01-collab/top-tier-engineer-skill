#!/usr/bin/env python3
"""checkup.py: one report on a codebase's structure, ranked by where changes land.

The fixture repo has an ugly function nobody changes (idle), a pair of files that keep changing
together with fixes and no import between them, two HTTP libraries, a dead module, a copy in a
git-ignored folder and an untracked file. Run with `python -m unittest discover tests`.
"""
import json, os, re, shutil, subprocess, sys, tempfile, unittest

from _helpers import ROOT, SCRIPTS, run

UGLY = "def decide(a, b, c, d):\n" + "".join(
    f"    {'if' if i == 0 else 'elif'} a == {i} and (b or c or d):\n        return {i}\n" for i in range(18)
) + "    return -1\n"


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def write(repo, rel, text):
    p = os.path.join(repo, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def commit(repo, msg):
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", msg)
    return git(repo, "rev-parse", "--short=8", "HEAD")


def fixture(repo):
    git(repo, "init", "-q")
    write(repo, "main.py", "from orders import total\nfrom invoices import bill\nfrom ugly import decide\n"
                           "from client_a import fetch\nfrom client_b import ping\n\n"
                           "if __name__ == '__main__':\n    print(total([1]), bill(1), decide(1, 1, 1, 1))\n")
    write(repo, "ugly.py", UGLY)
    write(repo, "orders.py", "TAX = 7\n\ndef total(xs):\n    return sum(xs) * (100 + TAX) // 100\n")
    write(repo, "invoices.py", "TAX = 7\n\ndef bill(x):\n    return x * (100 + TAX) // 100\n")
    write(repo, "client_a.py", "import urllib.request\n\ndef fetch(u):\n    return urllib.request.urlopen(u)\n")
    write(repo, "client_b.py", "import http.client\n\ndef ping(h):\n    return http.client.HTTPConnection(h)\n")
    write(repo, "old_report.py", "def build():\n    return 'report'\n")
    write(repo, ".gitignore", "wt/\n")
    write(repo, "wt/copy/old_thing.py", "def lost():\n    return 1\n")
    commit(repo, "start")
    shas = []
    for i in range(6):
        kind = "fix" if i % 2 else "change"
        write(repo, "orders.py", f"TAX = {8 + i}\n\ndef total(xs):\n    return sum(xs) * (100 + TAX) // 100\n")
        write(repo, "invoices.py", f"TAX = {8 + i}\n\ndef bill(x):\n    return x * (100 + TAX) // 100\n")
        write(repo, "tests/test_orders.py", f"from orders import total\n\ndef test_total():\n    assert total([100]) == {108 + i}\n")
        shas.append(commit(repo, f"{kind} tax rate {i}"))
    write(repo, "untracked_mess.py", "def nobody():\n    return 2\n")
    return shas


def checkup(repo, *args):
    return run("checkup.py", repo, "--recent", "4", *args)


def report(repo):
    code, out, err = checkup(repo, "--json")
    assert code == 0, out + err
    return json.loads(out)


def notes(repo, account=(), answer=(), read=None):
    if read is None:
        read = READ_ALL
    with open(os.path.join(repo, ".checkup", "notes.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Checkup notes\n\n## account\n" + "".join(f"- {a}\n" for a in account)
                 + "\n## read\n" + "".join(f"- {a}\n" for a in read)
                 + "\n## answer\n" + "".join(f"- {a}\n" for a in answer))


# One line per file the fixture's report asks to read; client_b carries the one risk.
READ_ALL = [
    "orders.py: nothing: total(): sums the items and adds tax",
    "invoices.py: nothing: bill(): adds tax to one amount",
    "main.py: nothing: total(): prints one of each result",
    "ugly.py: nothing: decide(): maps a code to a number",
    "client_a.py: nothing: fetch(): opens one url",
    "client_b.py: risk: ping(): opens a connection and never closes it",
    "old_report.py: nothing: build(): returns a fixed string",
]


class Report(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.shas = fixture(cls.tmp)
        cls.r = report(cls.tmp)
        cls.ids = [f["id"] for f in cls.r["findings"]]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_report_opens_with_what_was_measured(self):
        code, out, _ = checkup(self.tmp)
        self.assertEqual(code, 0)
        first = out.splitlines()[0]
        self.assertTrue(first.startswith("Measured:"), first)
        self.assertIn("tracked files", first)
        self.assertLess(out.index("Measured:"), out.index("weight"))

    def test_the_pair_that_changes_together_ranks_above_the_idle_ugly_function(self):
        pair = "locality/pair@invoices.py+orders.py"
        self.assertEqual(self.ids[0], pair, self.ids)
        f = self.r["findings"][0]
        self.assertEqual((f["commits"], f["fixes"], f["weight"]), (7, 3, 13))  # start + 6 rate changes
        self.assertIn("no import between them", f["detail"])
        ugly = next(f for f in self.r["findings"] if f["id"].startswith("depth/tangled@ugly.py"))
        self.assertTrue(ugly["idle"])
        self.assertEqual(ugly["weight"], 1)

    def test_a_test_and_its_code_changing_together_is_not_a_pair(self):
        pairs = [i for i in self.ids if i.startswith("locality/")]
        self.assertEqual(pairs, ["locality/pair@invoices.py+orders.py"])

    def test_two_libraries_for_one_job_are_one_finding(self):
        f = next(f for f in self.r["findings"] if f["id"] == "oneway/two-ways@http")
        self.assertEqual(f["files"], ["client_a.py", "client_b.py"])

    def test_dead_code_is_reported_and_stays_dead_on_a_rerun(self):
        self.assertIn("dead/dead-module@old_report.py", self.ids)
        code, out, err = checkup(self.tmp, "--json", "--fresh")
        self.assertIn("dead/dead-module@old_report.py", [f["id"] for f in json.loads(out)["findings"]])

    def test_ignored_and_untracked_paths_are_not_the_codebase(self):
        text = json.dumps(self.r["findings"])
        self.assertNotIn("wt/", text)
        self.assertNotIn("untracked_mess", text)
        self.assertGreaterEqual(self.r["dropped"], 1)

    def test_a_section_nothing_measured_says_not_checked(self):
        s = self.r["sections"]
        self.assertFalse(s["tests"]["measured"])
        self.assertIn("verify-loop", s["tests"]["why"])
        self.assertFalse(s["find"]["measured"])
        self.assertIn("FEATURES.md", s["find"]["why"])
        code, out, _ = checkup(self.tmp)
        self.assertIn("## Tests that can fail: not checked:", out)
        for k in ("locality", "direction", "depth", "oneway", "io", "dead"):
            self.assertTrue(s[k]["measured"], k)

    def test_layers_not_declared_is_said_not_passed(self):
        self.assertTrue(any("layers not checked" in n for n in self.r["sections"]["direction"]["notes"]))


class Cache(unittest.TestCase):
    def test_the_report_is_reused_only_while_the_tracked_tree_is_the_same(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture(tmp)
            a = report(tmp)
            path = os.path.join(tmp, ".checkup", "report.json")
            stamp = os.path.getmtime(path)
            self.assertEqual(report(tmp)["hash"], a["hash"])
            self.assertEqual(os.path.getmtime(path), stamp)
            write(tmp, "orders.py", "def total(xs):\n    return 0\n")
            self.assertNotEqual(report(tmp)["hash"], a["hash"])


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.shas = fixture(self.tmp)
        self.r = report(self.tmp)
        self.top = [f["id"] for f in self.r["findings"]]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def gate(self):
        return checkup(self.tmp, "--gate")

    def test_stage2_drafts_slots_for_the_top_three_and_stays_open(self):
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("1. Measure: holds.", out)
        self.assertIn("2. Account: OPEN", out)
        with open(os.path.join(self.tmp, ".checkup", "notes.md"), encoding="utf-8") as fh:
            text = fh.read()
        for i in self.top[:3]:
            self.assertIn(f"- {i}: [[fill", text)

    def test_a_cost_must_cite_a_commit_that_touched_the_files(self):
        pair = self.top[0]
        write(self.tmp, "other.txt", "x\n")
        git(self.tmp, "add", "other.txt")
        git(self.tmp, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "unrelated")
        other = git(self.tmp, "rev-parse", "--short=8", "HEAD")
        self.r = report(self.tmp)
        notes(self.tmp, [f"{pair}: cost: deadbeef1 and {other} show it"])
        code, out, _ = self.gate()
        self.assertIn(f"{pair}: a cost cites a commit that touched", out)
        notes(self.tmp, [f"{pair}: cost: {self.shas[1]} changed the tax rate in both files"])
        code, out, _ = self.gate()
        self.assertNotIn(f"{pair}: a cost cites", out)

    def test_none_needs_a_reason_and_hands_its_slot_to_the_next_finding(self):
        notes(self.tmp, [f"{self.top[0]}: none:"])
        code, out, _ = self.gate()
        self.assertIn("`none:` needs the reason", out)
        notes(self.tmp, [f"{self.top[0]}: none: the tax rate is meant to differ per product"])
        self.gate()
        with open(os.path.join(self.tmp, ".checkup", "notes.md"), encoding="utf-8") as fh:
            text = fh.read()
        for i in self.top[1:4]:
            self.assertIn(f"- {i}: [[fill", text)

    def test_a_note_for_a_finding_the_report_does_not_hold_fails(self):
        notes(self.tmp, ["depth/tangled@nowhere.py:1: cost: abc1234 made it worse"])
        code, out, _ = self.gate()
        self.assertIn("the report holds no such finding now", out)

    def test_an_idle_finding_costs_the_coming_change(self):
        ugly = next(f["id"] for f in self.r["findings"] if f["id"].startswith("depth/tangled@ugly.py"))
        notes(self.tmp, [f"{ugly}: cost: next:"])
        code, out, _ = self.gate()
        self.assertIn("`cost: next:` needs the coming change", out)
        notes(self.tmp, [f"{ugly}: cost: next: the planned discount tiers add five more branches"])
        code, out, _ = self.gate()
        self.assertNotIn(f"{ugly}: ", out.split("2. Account")[1].split("CHECKUP-GATE")[0]
                         if "2. Account: OPEN" in out else "")

    def account_all(self):
        """Fill the account so that exactly the pair and the two-ways finding carry a cost."""
        lines, kept = [], 0
        for f in self.r["findings"]:
            if f["id"] == "locality/pair@invoices.py+orders.py":
                lines.append(f"{f['id']}: cost: {self.shas[1]} and {self.shas[3]} fixed the rate twice")
            elif f["id"] == "oneway/two-ways@http":
                lines.append(f"{f['id']}: cost: next: the retry policy must be written twice")
            else:
                lines.append(f"{f['id']}: none: a fixture file, never changed on purpose")
        return lines

    def test_stage3_verdicts_follow_the_measurement(self):
        acc = self.account_all()
        notes(self.tmp, acc, ["locality: good", "tests: poor", "find: not checked", "direction: not checked",
                              "depth: good", "oneway: poor", "io: good", "dead: in places",
                              "fix 1: oneway/two-ways@http", "fix 2: locality/pair@invoices.py+orders.py"])
        code, out, _ = self.gate()
        self.assertIn("3. Read: holds.", out)
        self.assertIn("- locality: not `good` while", out)
        self.assertIn("- tests: nothing measured it", out)
        self.assertIn("- direction: it was measured", out)
        self.assertIn("- fix 1: should be locality/pair@invoices.py+orders.py", out)
        self.assertEqual(code, 1)

    def test_stage3_done_prints_the_answer(self):
        notes(self.tmp, self.account_all(), [
            "find: not checked", "locality: poor", "direction: good", "depth: in places",
            "oneway: poor", "io: good", "dead: in places", "tests: not checked",
            "fix 1: locality/pair@invoices.py+orders.py", "fix 2: oneway/two-ways@http"])
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)
        self.assertIn("CHECKUP-GATE: done", out)
        answer = out.split("ANSWER", 1)[1]
        self.assertTrue(answer.strip().startswith("Measured:"))
        self.assertIn("- Tests that can fail: not checked", answer)
        self.assertLess(answer.index("1. changed together"), answer.index("2. http is done with 2 libraries"))
        # What reading found comes before the structure fixes, and only the risks are listed.
        self.assertIn("- client_b.py ping(): opens a connection and never closes it", answer)
        self.assertLess(answer.index("ping()"), answer.index("Fix first:"))
        self.assertNotIn("decide()", answer)

    def test_a_drafted_slot_never_hides_the_agents_own_line(self):
        """Seen in an eval run: the agent's lines came first, the gate's slots after them, and
        the gate read the slots, stayed open, and sent the agent into its source."""
        answer = ["find: not checked", "locality: poor", "direction: good", "depth: in places",
                  "oneway: poor", "io: good", "dead: in places", "tests: not checked",
                  "fix 1: locality/pair@invoices.py+orders.py", "fix 2: oneway/two-ways@http"]
        slots = [f"{k}: [[fill: good | in places | poor | not checked]]" for k in
                 ("find", "locality", "direction", "depth", "oneway", "io", "dead", "tests")]
        slots += ["fix 1: [[fill: a finding id]]", "fix 2: [[fill: a finding id]]"]
        acc = self.account_all() + [self.account_all()[0].split(": ", 1)[0] + ": [[fill: cost: <commits> | none: <why>]]"]
        notes(self.tmp, acc, answer + slots)
        code, out, _ = self.gate()
        self.assertEqual(code, 0, out)

    def test_stage3_drafts_a_line_per_file_where_changes_land(self):
        due = self.r["read_due"]
        self.assertEqual(due[:2], ["invoices.py", "orders.py"])  # weight 13 each, then the rest
        self.assertNotIn("tests/test_orders.py", due)
        self.assertNotIn("untracked_mess.py", due)
        notes(self.tmp, self.account_all(), read=[])
        code, out, _ = self.gate()
        self.assertIn("3. Read: OPEN", out)
        with open(os.path.join(self.tmp, ".checkup", "notes.md"), encoding="utf-8") as fh:
            text = fh.read().split("## read", 1)[1].split("## answer")[0]
        for p in due:
            self.assertIn(f"- {p}: [[fill", text)

    def test_a_read_line_names_something_in_the_file_and_says_what(self):
        bad = [x for x in READ_ALL if not x.startswith(("client_b", "ugly", "orders"))] + [
            "client_b.py: risk: charge(): retries the post and pays twice",
            "ugly.py: risk: decide(): bad",
            "orders.py: looks fine",
            "nowhere.py: nothing: total(): sums things up here",
        ]
        notes(self.tmp, self.account_all(), read=bad)
        code, out, _ = self.gate()
        self.assertEqual(code, 1)
        self.assertIn("- client_b.py: charge() is not in that file", out)
        self.assertIn("- ugly.py: say what decide() can get wrong", out)
        self.assertIn("- orders.py: start with `risk: <name>():`", out)
        self.assertIn("- nowhere.py: not a tracked file", out)

    def test_poor_needs_a_cost_and_in_places_needs_a_finding(self):
        notes(self.tmp, self.account_all(), ["direction: poor"])
        code, out, _ = self.gate()
        self.assertIn("- direction: `poor` needs a finding in it with a cost", out)


class Shape(unittest.TestCase):
    def test_skill_body_is_short_and_shaped_like_its_siblings(self):
        with open(os.path.join(ROOT, "plugin", "skills", "checkup", "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        body = text.split("---", 2)[2]
        self.assertLessEqual(len(body), 5000)
        self.assertIn("disable-model-invocation: true", text)
        for part in ("**Goal:**", "`C` is `python", "| Stage | Holds when |", "CHECKUP-GATE: done"):
            self.assertIn(part, body)

    def test_the_helpers_it_runs_skip_its_state(self):
        """Otherwise a rerun reads module names in .checkup/report.json and calls dead code live."""
        for tool in ("graph-audit.py", "structure-report.py"):
            with open(os.path.join(SCRIPTS[tool], tool), encoding="utf-8") as fh:
                self.assertIn('".checkup"', fh.read(), f"{tool} does not skip .checkup/")


class Standalone(unittest.TestCase):
    def test_without_siblings_every_section_is_not_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = os.path.join(tmp, "skills", "checkup", "scripts")
            os.makedirs(skills)
            for f in ("checkup.py", "_encoding.py"):
                shutil.copy(os.path.join(SCRIPTS["checkup.py"], f), skills)
            repo = os.path.join(tmp, "repo")
            os.makedirs(repo)
            fixture(repo)
            p = subprocess.run([sys.executable, os.path.join(skills, "checkup.py"), repo, "--json"],
                               capture_output=True, text=True, encoding="utf-8")
            r = json.loads(p.stdout)
            # The history is checkup's own read, so locality is measured; nothing else is.
            self.assertEqual({f["section"] for f in r["findings"]}, {"locality"})
            self.assertEqual([k for k, s in r["sections"].items() if s["measured"]], ["locality"])
            self.assertEqual(r["probes"]["structure"]["status"], "missing")
            self.assertIn("not installed", r["sections"]["depth"]["why"])

    def test_not_a_git_repo_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("checkup.py", tmp)
            self.assertEqual(code, 2)
            self.assertIn("not a git repository", out)


if __name__ == "__main__":
    unittest.main()
