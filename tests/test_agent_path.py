"""The lazy path is the correct path.

An agent reads SKILL.md once, runs the first command it shows, follows what the output says and stops
as soon as it believes it has an answer. These tests hold the helper to that reader: one command
answers a question, every rejection says what would pass, the answer the helper drafts passes its own
gate once the judgment slots are filled, and nothing the agent needs is only in a file it will not open.
"""
import json, os, re, tempfile, unittest

from _helpers import ROOT, run
from test_gates import BAD, GOOD, TEST, project, prove, write

SKILL = os.path.join(ROOT, "plugin", "skills", "verify-loop")
FILL = re.compile(r"\[\[fill:[^\]]*\]\]")


def listing(root):
    return sorted(os.path.relpath(os.path.join(h, n), root)
                  for h, dirs, files in os.walk(root) if ".git" not in h for n in dirs + files)


def draft_of(out):
    """The ANSWER DRAFT block a command printed, without its header line."""
    lines = out.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith("ANSWER DRAFT"))
    body = []
    for ln in lines[start + 1:]:
        if ln.startswith("ANSWER-CHECK") or ln.startswith("Then:"):
            break
        body.append(ln)
    return "\n".join(body) + "\n"


def filled(draft):
    return FILL.sub("Total adds two numbers, per the spec", draft)


class AnswerCheckSaysWhatWouldPass(unittest.TestCase):
    """A bare MISSING sent agents into the helper's source. A rejection now carries its fix."""

    def check(self, root, text, *flags):
        with tempfile.TemporaryDirectory() as out_dir:
            path = os.path.join(out_dir, "answer.md")
            write(out_dir, "answer.md", text)
            return run("verify.py", "answer-check", root, "--answer", path, *flags)

    def test_every_problem_comes_with_a_line_that_fixes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp, extra="\n## Blind spots\n- the payment gateway is stubbed\n")
            write(tmp, "search.py", "def search(q):\n    return []\n")
            prove(tmp)
            code, out, _ = self.check(tmp, "Looks good.\n")
            self.assertEqual(code, 1, out)
            fixes = out.split("ADD THESE LINES", 1)[1].splitlines()[1:]
            self.assertIn("VERDICT: red", fixes)
            self.assertIn("GAP unmapped: search.py", fixes)
            self.assertIn("GAP blind spot: the payment gateway is stubbed", fixes)
            code, out, _ = self.check(tmp, "Looks good.\n" + "\n".join(fixes) + "\n")
            self.assertEqual(code, 0, out)

    def test_json_problems_carry_the_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "calc.py", BAD)
            run("verify.py", "run", tmp)
            code, out, _ = self.check(tmp, "Total: ready to merge.\n", "--json")
            problems = json.loads(out)["problems"]
            self.assertTrue(all(p.get("fix") for p in problems), problems)
            fixes = {p["kind"]: p["fix"] for p in problems}
            self.assertEqual(fixes["NO VERDICT"], "VERDICT: red")
            self.assertIn("ready to merge", fixes["OVERCLAIM"])

    def test_an_unfilled_slot_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            prove(tmp)
            code, out, _ = self.check(tmp, "VERDICT: green\nClaim: [[fill: the claim]]\n")
            self.assertEqual(code, 1, out)
            self.assertIn("ANSWER UNFILLED", out)


class ReportDraftsTheAnswer(unittest.TestCase):
    """The agent's cheapest move is to copy what it was shown. Make the copy correct."""

    def assert_draft_passes(self, root, out, *flags):
        draft = draft_of(out)
        self.assertRegex(draft, FILL, "the draft leaves the judgment to the agent")
        with tempfile.TemporaryDirectory() as out_dir:
            path = os.path.join(out_dir, "answer.md")
            write(out_dir, "answer.md", draft)
            code, msg, _ = run("verify.py", "answer-check", root, "--answer", path, *flags)
            self.assertEqual(code, 1, "a copied draft with its slots unfilled must not pass")
            write(out_dir, "answer.md", filled(draft))
            code, msg, _ = run("verify.py", "answer-check", root, "--answer", path, *flags)
            self.assertEqual(code, 0, msg + "\n---\n" + filled(draft))

    def test_the_draft_names_every_gap_and_passes_once_filled(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp, extra="\n## Blind spots\n- the payment gateway is stubbed\n")
            write(tmp, "search.py", "def search(q):\n    return []\n")
            prove(tmp)
            code, out, _ = run("verify.py", "report", tmp)
            self.assertIn("ANSWER DRAFT", out)
            self.assert_draft_passes(tmp, out)

    def test_a_red_draft_makes_no_claim_the_verdict_does_not_support(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "calc.py", BAD)
            run("verify.py", "run", tmp)
            code, out, _ = run("verify.py", "report", tmp)
            self.assertIn("VERDICT: red", draft_of(out))
            self.assert_draft_passes(tmp, out)

    def test_a_green_draft_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            prove(tmp)
            code, out, _ = run("verify.py", "report", tmp)
            self.assertEqual(code, 0, out)
            self.assert_draft_passes(tmp, out)

    def test_json_stays_the_machine_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            prove(tmp)
            a = json.loads(run("verify.py", "report", tmp, "--json")[1])
            self.assertNotIn("draft", a, "report --json equals status --json; the draft is for agents")


class OneCallAssess(unittest.TestCase):
    """Three commands became four or five in eval runs. A question gets one command."""

    def test_assess_runs_challenges_reports_and_drafts_without_touching_the_repo(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as state:
            project(tmp)
            before = listing(tmp)
            env_flag = ("--state-dir", state)
            code, out, _ = run("verify.py", "assess", tmp, *env_flag)
            self.assertEqual(listing(tmp), before, "assess must leave the repo as it was")
            self.assertIn("VERIFY:", out)
            self.assertIn("CHALLENGE-AUTO:", out)
            self.assertIn("VERDICT:", out)
            self.assertIn("ANSWER DRAFT", out)
            self.assertIn("answer-check", out.split("ANSWER DRAFT", 1)[1])
            self.assert_follow_up_finds_the_state(tmp, out, env_flag)

    def assert_follow_up_finds_the_state(self, tmp, out, flags):
        draft = filled(draft_of(out))
        with tempfile.TemporaryDirectory() as out_dir:
            path = os.path.join(out_dir, "answer.md")
            write(out_dir, "answer.md", draft)
            code, msg, _ = run("verify.py", "answer-check", tmp, "--answer", path, *flags)
            self.assertEqual(code, 0, msg + "\n---\n" + draft)

    def test_assess_defaults_to_temp_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            before = listing(tmp)
            code, out, _ = run("verify.py", "assess", tmp)
            self.assertEqual(listing(tmp), before)
            self.assertIn("--assess", out.split("ANSWER DRAFT", 1)[1],
                          "the printed follow-up must find the same temp state")

    def test_a_check_that_misses_a_planted_wrong_result_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "test_calc.py", TEST.replace("total(40, 2), 42", "total(0, 0), 0"))
            code, out, _ = run("verify.py", "assess", tmp)
            self.assertNotEqual(code, 0, out)
            self.assertRegex(out, r"SURVIVED|UNCOVERED")
            draft = draft_of(out)
            self.assertIn("GAP survived a wrong result: calc.py:", draft, "a copied draft must keep the survivor")
            with tempfile.TemporaryDirectory() as out_dir:
                path = os.path.join(out_dir, "answer.md")
                write(out_dir, "answer.md", "VERDICT: partial. Total passes and was never seen red.\n")
                code, msg, _ = run("verify.py", "answer-check", tmp, "--assess", "--answer", path)
                self.assertIn("GAP survived: calc.py", msg, "answer-check asks for the survivor")

    def test_a_feature_with_no_path_is_surveyed_through_what_its_checks_imported(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "VERIFY.md", "## Total\n- test: `python -m unittest test_calc.py`\n")
            write(tmp, "test_calc.py", TEST.replace("total(40, 2), 42", "total(0, 0), 0"))
            code, out, _ = run("verify.py", "assess", tmp)
            self.assertIn("surveying what its checks imported: calc.py", out)
            self.assertRegex(out, r"SURVIVED|UNCOVERED")

    def test_no_recipe_says_how_to_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "calc.py", GOOD)
            code, out, _ = run("verify.py", "assess", tmp)
            self.assertEqual(code, 2, out)
            self.assertIn("VERIFY.md", out)
            self.assertEqual(listing(tmp), ["calc.py"])


class AssessSaysWhatItSaw(unittest.TestCase):
    """An agent copies the draft. A draft that says nothing went red after the survey saw every
    wrong result caught hands the agent a false line, and calls a healthy check fake."""

    def test_a_caught_survey_is_not_reported_as_nothing_seen_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            code, out, _ = run("verify.py", "assess", tmp)
            self.assertRegex(out, r"CHALLENGE-AUTO: (\d+)/\1 caught", out)
            draft = draft_of(out)
            self.assertNotIn("no check here has been seen rejecting a wrong result", draft)
            self.assertRegex(draft, r"Total caught (\d+)/\1 wrong results", draft)
            self.assertIn("not a fail-proof receipt", draft)
            self.assertNotIn("nothing here is proven able to fail", out)

    def test_a_read_only_question_is_not_sent_to_more_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            code, out, _ = run("verify.py", "assess", tmp)
            self.assertNotIn("run --strict", out, "assess answers; it does not ask for a strict run")
            self.assertNotIn("SWARM:", out, "a report does not start helper agents")
            self.assertIn("advance", out.split("ANSWER DRAFT", 1)[0])


class AdvanceOutputIsReadable(unittest.TestCase):
    """What a step printed is evidence when it failed and noise when it passed."""

    def test_a_passing_step_keeps_its_summary_and_a_failing_one_keeps_its_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "calc.py", BAD)
            code, out, _ = run("verify.py", "advance", tmp, "--json")
            steps = json.loads(out)["steps"]
            self.assertIn("expected total 42", steps[0]["output"])
            write(tmp, "calc.py", GOOD)
            code, out, _ = run("verify.py", "advance", tmp, "--json")
            result = json.loads(out)
            self.assertEqual(result["stop"], "done", out)
            for step in result["steps"]:
                if step["exit"] == 0:
                    self.assertLessEqual(len(step["output"].splitlines()), 3, step)

    def test_plain_advance_shows_why_a_step_failed_and_drafts_the_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            project(tmp)
            write(tmp, "calc.py", BAD)
            code, out, _ = run("verify.py", "advance", tmp)
            self.assertIn("expected total 42", out)
            self.assertIn("ANSWER DRAFT", out)


class SkillDocIsCheap(unittest.TestCase):
    """SKILL.md is paid for on every trigger. It routes; the output teaches."""

    def read(self, rel):
        with open(os.path.join(SKILL, rel), encoding="utf-8") as fh:
            return fh.read()

    def body(self):
        return self.read("SKILL.md").split("---", 2)[2]

    def test_the_body_fits_its_budget(self):
        lines = self.body().strip().splitlines()
        # Characters are what every trigger pays for; lines only keep tables from sprawling.
        self.assertLessEqual(len(self.body()), 5000, "SKILL.md routes; move lookups to references/ or into the output")
        self.assertLessEqual(len(lines), 80)

    def test_the_description_fits(self):
        front = self.read("SKILL.md").split("---", 2)[1]
        desc = " ".join(front.split("description:", 1)[1].split("metadata:", 1)[0].replace(">-", "").split())
        self.assertLessEqual(len(desc), 400, desc)

    def test_every_command_it_names_exists(self):
        _, out, _ = run("verify.py", "--help")
        commands = set(re.findall(r"^\s{4}(\S+)\s", out, re.M)) | set(
            re.search(r"\{([^}]*)\}", out).group(1).split(","))
        for doc in ["SKILL.md"] + ["references/" + n for n in os.listdir(os.path.join(SKILL, "references"))]:
            for cmd in re.findall(r"[`/]verify\.py\s+([a-z][a-z-]+)", self.read(doc)):
                self.assertIn(cmd, commands, f"{doc} names `verify.py {cmd}`, which does not exist")

    def test_every_link_resolves(self):
        docs = ["SKILL.md", "VERIFY_FORMAT.md"] + ["references/" + n for n in os.listdir(os.path.join(SKILL, "references"))]
        for doc in docs:
            for target in re.findall(r"\]\(([^)#\s]+\.md)(?:#([^)\s]+))?\)", self.read(doc)):
                rel, anchor = target
                path = os.path.normpath(os.path.join(os.path.dirname(doc), rel))
                self.assertTrue(os.path.isfile(os.path.join(SKILL, path)), f"{doc} links {rel}")
                if anchor:
                    heads = [re.sub(r"[^\w\- ]", "", h).strip().lower().replace(" ", "-")
                             for h in re.findall(r"^#+\s+(.*)$", self.read(path), re.M)]
                    self.assertIn(anchor, heads, f"{doc} links {rel}#{anchor}")

    def test_every_verdict_it_names_is_one_the_helper_prints(self):
        scripts = "".join(self.read(os.path.join("scripts", n)) for n in os.listdir(os.path.join(SKILL, "scripts"))
                          if n.endswith(".py"))
        for word in set(re.findall(r"`([A-Z][A-Z ]{3,}[A-Z](?: x2)?)`", self.body())):
            self.assertIn(word, scripts, f"SKILL.md names `{word}`, which no script prints")


if __name__ == "__main__":
    unittest.main()
