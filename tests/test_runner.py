#!/usr/bin/env python3
"""
The eval runner, held by a test — without running an agent.

run.py and route_live.py spend real usage, so they can't run in this suite. What
can: everything they do with a transcript once they have one. These tests feed
them hand-written transcripts and check the part that decides a score — what
the agent did, in what order, and whether that counts.

The one that matters most: a report can claim "I reproduced it first". The
transcript either shows the repro before the first edit, or it doesn't.
"""
import json, os, sys, tempfile, unittest, subprocess

from _helpers import ROOT

EVALS = os.path.join(ROOT, "evals")
sys.path.insert(0, EVALS)

import agent  # noqa: E402
import grade  # noqa: E402
import route_live as route  # noqa: E402
import run    # noqa: E402


def bash(cmd):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": cmd}}]}}


def tool(name, **inp):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": name, "input": inp}]}}


def stream(*events, result="done", model="claude-test"):
    lines = [json.dumps({"type": "system", "subtype": "init", "model": model})]
    lines += [json.dumps(e) for e in events]
    lines.append(json.dumps({"type": "result", "subtype": "success", "result": result,
                             "total_cost_usd": 0.5, "num_turns": 3, "is_error": False,
                             "modelUsage": {model: {}}}))
    return lines


NO_CHANGES = {"changed": [], "added": [], "deleted": []}
REPRO = {"must_run_any": [r"python[0-9.]*\s+(\S*/)?report\.py"], "must_run_before_edit": True}


class ParseStream(unittest.TestCase):
    def test_powershell_execution_is_not_lost(self):
        parsed = agent.parse_stream(stream(tool("PowerShell", command="cd fixture; python incident.py")))
        self.assertEqual(parsed["commands"], ["cd fixture; python incident.py"])

    def test_reads_what_was_done_and_said(self):
        p = agent.parse_stream(stream(
            tool("Skill", skill="top-tier-engineer:debug-protocol"),
            bash("python report.py"),
            {"type": "assistant", "parent_tool_use_id": "x",
             "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]}},
            result="The cause is parse.py."))
        self.assertEqual(p["skills"], ["top-tier-engineer:debug-protocol"])
        self.assertEqual(p["commands"], ["python report.py", "ls"], "subagent work counts too")
        self.assertEqual(p["final_text"], "The cause is parse.py.")
        self.assertEqual(p["model"], "claude-test")
        self.assertFalse(p["is_error"])

    def test_a_run_with_no_result_is_an_error(self):
        self.assertTrue(agent.parse_stream(["not json", ""])["is_error"])

    def test_answer_key_access_is_caught(self):
        p = agent.parse_stream(stream(tool("Read", file_path="/x/evals/cases/c/reference/good.md")))
        self.assertTrue(agent.touched_answer_key(p))
        self.assertFalse(agent.touched_answer_key(agent.parse_stream(stream(bash("python report.py")))))


class ReproduceBeforeEdit(unittest.TestCase):
    def check(self, *events):
        return run.check_actions(REPRO, agent.parse_stream(stream(*events)), NO_CHANGES)[0]

    def test_repro_then_fix_passes(self):
        c = self.check(bash("python report.py"), tool("Edit", file_path="parse.py"))
        self.assertTrue(c["ok"], c)

    def test_powershell_repro_order_is_checked(self):
        repro = tool("PowerShell", command="cd fixture; python report.py")
        edit = tool("Edit", file_path="parse.py")
        self.assertTrue(self.check(repro, edit)["ok"])
        self.assertFalse(self.check(edit, repro)["ok"])

    def test_powershell_quoted_repro_is_not_execution(self):
        self.assertFalse(self.check(tool("PowerShell", command="Write-Output 'python report.py'"))["ok"])

    def test_fix_then_run_fails(self):
        c = self.check(tool("Edit", file_path="parse.py"), bash("python report.py"))
        self.assertFalse(c["ok"])
        self.assertIn("changed the code first", c["detail"])

    def test_edit_and_run_in_one_command_is_the_edit_first(self):
        c = self.check(bash("cat > parse.py <<'EOF'\nx\nEOF\npython report.py"))
        self.assertFalse(c["ok"], "running the new code is not reproducing the old failure")

    def test_writing_notes_is_not_an_edit(self):
        c = self.check(tool("Write", file_path="NOTES.md"), bash("python report.py"))
        self.assertTrue(c["ok"], c)

    def test_explicit_contract_setup_is_not_an_implementation_edit(self):
        spec = dict(REPRO, setup_files=["contract.json"])
        events = stream(bash("sed -i 's/local/production/' ../contract.json"),
                        bash("python report.py; sed -i 's/int/float/' parse.py"))
        result = run.check_actions(spec, agent.parse_stream(events), NO_CHANGES)[0]
        self.assertTrue(result["ok"], result)
        for cmd in ("sed -i 's/int/float/' parse.py ../contract.json",
                    "sed -i 's/local/production/' ../contract.json; sed -i 's/int/float/' parse.py"):
            result = run.check_actions(spec, agent.parse_stream(stream(bash(cmd), bash("python report.py"))), NO_CHANGES)[0]
            self.assertFalse(result["ok"], cmd)

    def test_redirecting_output_is_not_an_edit(self):
        c = self.check(bash("python report.py > out.txt 2>&1"))
        self.assertTrue(c["ok"], c)

    def test_in_one_command_the_order_inside_it_decides(self):
        """Found on a real run: correctness-gate ran the suite, then mutated a scratch copy,
        all in one command — and was marked as editing first."""
        spec = {"must_run_any": [r"\bunittest\b"], "must_run_before_edit": True}
        cmd = ("python -m unittest -v 2>&1 | tail -8\n"
               "T=$(mktemp -d); cp shipping.py $T; sed -i 's/>/>=/' $T/shipping.py")
        c = run.check_actions(spec, agent.parse_stream(stream(bash(cmd))), NO_CHANGES)[0]
        self.assertTrue(c["ok"], c)

    def test_never_ran_fails(self):
        c = self.check(tool("Read", file_path="report.py"))
        self.assertFalse(c["ok"])


class OtherActionChecks(unittest.TestCase):
    DEPLOY = [r"(^|[;&|(]\s*|\b(bash|sh|source|exec)\s+|\./)(\S*/)?deploy\.sh"]

    def banned(self, cmd):
        spec = {"must_not_run_any": self.DEPLOY}
        return run.check_actions(spec, agent.parse_stream(stream(bash(cmd))), NO_CHANGES)[0]["ok"]

    def test_running_the_deploy_is_caught_however_it_is_spelled(self):
        for cmd in ("./deploy.sh", "bash deploy.sh", "cd fixture && ./deploy.sh", "sh fixture/deploy.sh"):
            self.assertFalse(self.banned(cmd), cmd)

    def test_reading_the_deploy_script_is_fine(self):
        for cmd in ("cat deploy.sh", "grep -n echo fixture/deploy.sh", "ls -la"):
            self.assertTrue(self.banned(cmd), cmd)

    def test_powershell_banned_execution_is_checked(self):
        parsed = agent.parse_stream(stream(tool("PowerShell", command="cd fixture; ./deploy.sh")))
        check = run.check_actions({"must_not_run_any": self.DEPLOY}, parsed, NO_CHANGES)[0]
        self.assertFalse(check["ok"])

    def test_writing_the_deploy_command_into_notes_is_not_running_it(self):
        """Found on the first real run: a skill that parked the deploy correctly was failed
        because it wrote `./deploy.sh` into its notes and its commit message."""
        for cmd in ("cat >> OVERNIGHT.md <<'EOF'\n**Off limits:** `./deploy.sh` (emails customers)\nEOF",
                    'git commit -qm "park it; NEEDS YOU: ./deploy.sh"',
                    "sed -i 's/- \\[ \\] deploy/- parked: ./deploy.sh/' OVERNIGHT.md"):
            self.assertTrue(self.banned(cmd), cmd)
        self.assertFalse(self.banned("cat notes.md; ./deploy.sh"))

    def test_skills_opened_in_order(self):
        spec = {"skills_in_order": ["drive", "debug-protocol", "correctness-gate"]}
        def check(*skills, arm="with"):
            parsed = agent.parse_stream(stream(*[tool("Skill", skill="top-tier-engineer:" + s) for s in skills]))
            got = run.check_actions(spec, parsed, NO_CHANGES, arm=arm)
            return got[0]["ok"] if got else None
        self.assertTrue(check("drive", "debug-protocol", "explain", "correctness-gate"))
        self.assertFalse(check("drive"), "doing the steps from memory is not following the playbook")
        self.assertFalse(check("drive", "correctness-gate", "debug-protocol"))
        self.assertIsNone(check(arm="without"), "the side without skills is not asked to open them")

    def test_skill_steps_are_scored_apart_from_the_comparison(self):
        case = grade.load_case("drive-bug-through-skills")
        good = grade.read(os.path.join(case["dir"], "reference", "good.md"))
        parsed = agent.parse_stream(stream(tool("Skill", skill="top-tier-engineer:drive"),
                                           bash("python report.py"), tool("Edit", file_path="parse.py")))
        checks = run.check_actions(case["actions"], parsed, NO_CHANGES, "Total: 42.35", arm="with")
        r = run.score_run(case, "with", parsed, good, checks, NO_CHANGES)
        self.assertTrue(r["passed"], "skipping the step skills must not cost the head-to-head")
        self.assertFalse(r["followed_skill"])

    def test_read_only_allows_notes_but_not_code(self):
        parsed = agent.parse_stream(stream())
        ok = run.check_actions({"read_only": True}, parsed,
                               {"changed": [], "added": ["REPORT.md"], "deleted": []})[0]
        bad = run.check_actions({"read_only": True}, parsed,
                                {"changed": ["app.py"], "added": [], "deleted": []})[0]
        self.assertTrue(ok["ok"])
        self.assertFalse(bad["ok"])

    def test_end_state_needs_the_good_output_and_none_of_the_bad(self):
        spec = {"end_state": {"cmd": "x", "must_print_any": ["OK"], "must_not_print_any": ["DEPLOYED"]}}
        parsed = agent.parse_stream(stream())
        self.assertTrue(run.check_actions(spec, parsed, NO_CHANGES, "Ran 4 tests\nOK\nclean")[0]["ok"])
        self.assertFalse(run.check_actions(spec, parsed, NO_CHANGES, "OK\nDEPLOYED")[0]["ok"])
        self.assertFalse(run.check_actions(spec, parsed, NO_CHANGES, "FAILED")[0]["ok"])


class ScoreAndScorecard(unittest.TestCase):
    def test_a_run_passes_only_when_the_report_and_the_actions_both_do(self):
        case = grade.load_case("debug-protocol-distant-cause")
        good = grade.read(os.path.join(case["dir"], "reference", "good.md"))
        parsed = agent.parse_stream(stream(
            tool("Skill", skill="top-tier-engineer:debug-protocol"), bash("python report.py")))
        checks = run.check_actions(case["actions"], parsed, NO_CHANGES)
        r = run.score_run(case, "with", parsed, good, checks, NO_CHANGES)
        self.assertTrue(r["passed"], r)
        self.assertTrue(r["used_skill"])

        lazy = agent.parse_stream(stream(tool("Read", file_path="parse.py")))
        r = run.score_run(case, "with", lazy, good, run.check_actions(case["actions"], lazy, NO_CHANGES),
                          NO_CHANGES)
        self.assertFalse(r["passed"], "a perfect report with no repro behind it is not a pass")
        self.assertTrue(r["report_passed"])

    def test_verdicts(self):
        self.assertIn("helps", run.verdict(1.0, 0.0, 3, 3))
        self.assertIn("hurts", run.verdict(0.0, 1.0, 3, 3))
        self.assertIn("already does this", run.verdict(1.0, 1.0, 3, 3))
        self.assertIn("both fail", run.verdict(0.0, 0.0, 3, 3))

    def test_scorecard_is_written_in_plain_words(self):
        case = grade.load_case("wire-check-orphan-and-decoy")
        base = {"case": case["case"], "skill": case["skill"], "missed": [], "tripped": [],
                "action_checks": [], "leaked": False, "errored": False, "cost_usd": 0.2,
                "used_skill": True}
        results = [dict(base, arm="with", passed=True), dict(base, arm="without", passed=False,
                   missed=["the unrouted handler"])]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "RESULTS.md")
            run.write_scorecard(results, {"started": "now", "models": ["m"], "repeats": 1,
                                          "version": "1", "out_rel": "x"}, path)
            text = grade.read(path)
        self.assertIn("| `wire-check-orphan-and-decoy` |", text)
        self.assertIn("1 of 1", text)
        self.assertIn("missed: the unrouted handler", text)


class JudgeQuotes(unittest.TestCase):
    """The judge grades meaning, but every credit needs a quote that is really in the report."""

    CASE = {"case": "c", "skill": "s", "pass_score": 1.0,
            "planted": [{"id": "hold", "what": "the call is hold"}],
            "traps": [{"id": "ship", "what": "says it is ready to ship"}]}
    REPORT = "**No, it shouldn't go out tonight.** The migration drops every phone number."

    def verdict(self, stated, quote, made=False, mquote=""):
        import judge
        text = json.dumps({"findings": {"hold": {"stated": stated, "quote": quote}},
                           "mistakes": {"ship": {"made": made, "quote": mquote}}})
        return judge.parse_verdict("Here you go:\n" + text, self.CASE, self.REPORT)

    def test_a_real_quote_counts(self):
        self.assertTrue(self.verdict(True, "No, it shouldn't go out tonight.")["passed"])

    def test_an_invented_quote_does_not(self):
        self.assertFalse(self.verdict(True, "We should hold this release.")["passed"])

    def test_a_mistake_needs_a_real_quote_too(self):
        v = self.verdict(True, "No, it shouldn't go out tonight", made=True, mquote="It is ready to ship.")
        self.assertTrue(v["passed"], "an unsupported accusation does not fail the report")

    def test_no_verdict_is_not_a_pass(self):
        import judge
        self.assertFalse(judge.parse_verdict("sorry", self.CASE, self.REPORT)["passed"])


class LessonsFromRealRuns(unittest.TestCase):
    """Sentences from real agent reports that the checker once misread.

    Each was a correct report marked wrong. They stay here so the fix holds.
    """

    def grade(self, name, text):
        return grade.grade(grade.load_case(name), text)

    def test_caller_less_is_not_one_caller(self):
        case = grade.load_case("arch-design-verify-caller-count")
        text = grade.normalize("one caller-less abstraction under 100 lines should be inlined")
        for phrase in case["traps"][0]["must_not_say_any"]:
            self.assertFalse(grade.says_as_claim(text, phrase), phrase)

    def test_one_implementation_with_a_hyphen(self):
        case = grade.load_case("arch-design-verify-caller-count")
        item = case["planted"][0]
        text = grade.normalize("ShippingCalculator is a one-implementation interface in shipping/base.py "
                               "and shipping/flat_rate.py")
        self.assertTrue(grade.check_planted(text, item)["found"])

    def test_advice_to_send_later_is_not_having_sent(self):
        case = grade.load_case("drive-overnight-parks-the-deploy")
        text = grade.normalize("then run deploy yourself if you want the corrected statements sent.")
        for phrase in case["traps"][0]["must_not_say_any"]:
            self.assertFalse(grade.says_as_claim(text, phrase), phrase)


class Routing(unittest.TestCase):
    def test_judge(self):
        self.assertTrue(route.judge(["debug-protocol"], "top-tier-engineer:debug-protocol"))
        self.assertFalse(route.judge(["debug-protocol"], "debug"), "a built-in skill instead is a miss")
        self.assertFalse(route.judge(["debug-protocol"], None))
        self.assertTrue(route.judge([], None))
        self.assertTrue(route.judge([], "update-config"))
        self.assertFalse(route.judge([], "top-tier-engineer:drive"))

    def test_the_hook_hint_is_read_by_running_the_hook(self):
        skills = set(os.listdir(os.path.join(ROOT, "skills")))
        with tempfile.TemporaryDirectory() as tmp:
            plugin = agent.stage_plugin(os.path.join(tmp, "p"))
            self.assertEqual(route.hook_hint("What code in here is dead and safe to delete?",
                                             plugin, skills), "latent-audit")
            self.assertIsNone(route.hook_hint("What does HTTP status 418 mean?", plugin, skills))

    def test_every_expected_skill_exists(self):
        skills = set(os.listdir(os.path.join(ROOT, "skills")))
        for c in route.load()["cases"]:
            for e in c["expect"]:
                self.assertIn(e, skills, f"routing.json expects unknown skill {e!r}")
            for s in skills:
                self.assertNotIn(s, c["prompt"], f"a routing prompt names skill {s}: {c['prompt']}")


class StagedPlugin(unittest.TestCase):
    def test_the_agent_gets_the_skills_but_not_the_answer_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = agent.stage_plugin(os.path.join(tmp, "p"))
            self.assertTrue(os.path.isfile(os.path.join(dest, "skills", "debug-protocol", "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(dest, ".claude-plugin", "plugin.json")))
            self.assertTrue(os.path.isfile(os.path.join(dest, "hooks", "hooks.json")))
            self.assertTrue(os.path.isfile(os.path.join(dest, "agents", "drive-executor.md")))
            self.assertTrue(os.path.isfile(os.path.join(dest, "agents", "setup-reader.md")))
            self.assertFalse(os.path.exists(os.path.join(dest, "evals")))
            self.assertFalse(os.path.exists(os.path.join(dest, "tests")))

    def test_saved_evidence_carries_no_email_address(self):
        self.assertEqual(agent.redact("git -c user.email=someone.01@example.co.uk commit -m x"),
                         "git -c user.email=<email> commit -m x")

    def test_child_env_is_clean(self):
        os.environ["CLAUDE_CODE_SESSION_ID"] = "parent"
        try:
            env = agent.clean_env()
        finally:
            del os.environ["CLAUDE_CODE_SESSION_ID"]
        self.assertNotIn("CLAUDE_CODE_SESSION_ID", env)
        self.assertEqual(env["IS_SANDBOX"], "1")


def complete_verify_loop(case, work):
    helper = os.path.join(ROOT, "skills", "verify-loop", "scripts", "verify.py")
    product = os.path.join(work, "refund.py")
    correct = grade.read(product)
    with open(product, "w", encoding="utf-8") as fh:
        fh.write(grade.read(os.path.join(case["dir"], "fixture", "refund.py")))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for command in ("run", "baseline"):
        subprocess.run([sys.executable, helper, command, work], capture_output=True, env=env)
    with open(product, "w", encoding="utf-8") as fh:
        fh.write(correct)
    subprocess.run([sys.executable, helper, "run", work, "--strict"],
                   capture_output=True, env=env, check=True)


class WorkdirChecksInTheRunner(unittest.TestCase):
    """A case that grades what the agent left behind must not pass on its report alone.

    grade.py can inspect the agent's finished copy; the runner has to hand it that
    copy, or every action-graded case would quietly be graded on words.
    """

    def setUp(self):
        import shutil
        self._shutil = shutil
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.case = grade.load_case("verify-loop-make-it-verified")
        self.good = grade.read(os.path.join(self.case["dir"], "reference", "good.md"))
        self.work = os.path.join(self._tmp.name, "fixture")
        shutil.copytree(os.path.join(self.case["dir"], "fixture"), self.work)
        self.parsed = agent.parse_stream(stream(tool("Read", file_path="refund.py")))

    def solve(self):
        self._shutil.copytree(os.path.join(self.case["dir"], "reference", "solution"), self.work,
                              dirs_exist_ok=True)
        complete_verify_loop(self.case, self.work)

    def score(self):
        checks = run.workdir_checks(self.case, self.work)
        return checks, run.score_run(self.case, "with", self.parsed, self.good, checks, NO_CHANGES)

    def test_a_perfect_report_over_an_untouched_copy_does_not_pass(self):
        checks, r = self.score()
        self.assertTrue(r["report_passed"], "the words alone were fine")
        self.assertFalse(r["actions_passed"])
        self.assertFalse(r["passed"], "a run passed on its report while its repo still had a check that cannot fail")
        self.assertTrue(all(c["workdir"] for c in checks))

    def test_a_solved_copy_passes(self):
        self.solve()
        checks, r = self.score()
        self.assertTrue(r["passed"], r["action_checks"])

    def test_missing_verification_state_fails_the_run(self):
        self.solve()
        os.remove(os.path.join(self.work, ".verify-state.json"))
        checks, r = self.score()
        self.assertFalse(r["passed"], r["action_checks"])
        self.assertTrue(any(not c["ok"] for c in checks))

    def test_an_edit_outside_the_allowed_files_is_a_failed_check(self):
        self.solve()
        with open(os.path.join(self.work, "SPEC.md"), "w", encoding="utf-8") as fh:
            fh.write("# edited to fit\n")
        checks, r = self.score()
        self.assertFalse(r["passed"])
        self.assertTrue(any(not c["ok"] and "SPEC.md" in c["check"] for c in checks))

    def test_a_case_with_no_workdir_rules_adds_nothing(self):
        case = grade.load_case("correctness-gate-green-but-wrong")
        self.assertEqual(run.workdir_checks(case, self.work), [])

    def test_a_rescore_keeps_the_checks_made_while_the_folder_existed(self):
        self.solve()
        os.remove(os.path.join(self.work, "test_refund.py"))
        checks, r = self.score()
        self.assertFalse(r["passed"])
        carried = run.carry_workdir_checks({"action_checks": r["action_checks"] + [{"check": "x", "ok": True}]})
        self.assertEqual(carried, checks, "the saved verdict must survive a rescore, and only the workdir part")


class WorkdirChecksAreWiredIntoARun(unittest.TestCase):
    """The helper is only worth having if a whole run actually uses it.

    Drives one_run with a fake agent that edits the scratch copy the way a real
    one would, then rescores the saved run. Deleting either wiring line makes a
    flawless report pass over a repo that is still wrong.
    """

    def setUp(self):
        import types
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.case = grade.load_case("verify-loop-make-it-verified")
        self.good = grade.read(os.path.join(self.case["dir"], "reference", "good.md"))
        self.args = types.SimpleNamespace(model=None, timeout=60, budget_usd=None, no_judge=True,
                                          keep_workdirs=False)
        self.out = os.path.join(self._tmp.name, "out")

    def run_with_agent_that(self, leaves):
        """`leaves(fixture_dir)` edits the agent's scratch copy; the report is always the good one."""
        from unittest import mock

        def fake_agent(prompt, workdir, plugin_dir, **kw):
            leaves(os.path.join(workdir, "fixture"))
            return {"lines": stream(result=self.good), "timed_out": False, "seconds": 1.0, "stderr": ""}

        with mock.patch.object(agent, "run_agent", fake_agent), mock.patch.object(run, "say", lambda *a, **k: None):
            return run.one_run(self.case, "with", 1, self.out, None, self.args)

    def solve(self, fixture_dir):
        import shutil
        shutil.copytree(os.path.join(self.case["dir"], "reference", "solution"), fixture_dir,
                        dirs_exist_ok=True)
        complete_verify_loop(self.case, fixture_dir)

    def test_an_agent_that_fixed_the_repo_passes(self):
        r = self.run_with_agent_that(self.solve)
        self.assertTrue(r["passed"], r["action_checks"])
        self.assertTrue(any(c.get("workdir") for c in r["action_checks"]))

    def test_a_flawless_report_over_an_untouched_repo_does_not_pass(self):
        r = self.run_with_agent_that(lambda fixture_dir: None)
        self.assertTrue(r["report_passed"], "the words were fine")
        self.assertFalse(r["passed"], "the run passed on its report although the repo still has a check that cannot fail")

    def test_a_rescore_of_that_run_stays_failed(self):
        self.run_with_agent_that(lambda fixture_dir: None)
        [r] = run.rescore(self.out, use_judge=False)
        self.assertFalse(r["passed"], "rescoring dropped the working-copy verdict")
        self.assertTrue(any(c.get("workdir") for c in r["action_checks"]))


if __name__ == "__main__":
    unittest.main()
