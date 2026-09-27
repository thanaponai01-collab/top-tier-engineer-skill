#!/usr/bin/env python3
"""
The eval runner, held by a test — without running an agent.

run.py and route.py spend real usage, so they can't run in this suite. What
can: everything they do with a transcript once they have one. These tests feed
them hand-written transcripts and check the part that decides a score — what
the agent did, in what order, and whether that counts.

The one that matters most: a report can claim "I reproduced it first". The
transcript either shows the repro before the first edit, or it doesn't.
"""
import json, os, sys, tempfile, unittest

from _helpers import ROOT

EVALS = os.path.join(ROOT, "evals")
sys.path.insert(0, EVALS)

import agent  # noqa: E402
import grade  # noqa: E402
import route  # noqa: E402
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

    def test_redirecting_output_is_not_an_edit(self):
        c = self.check(bash("python report.py > out.txt 2>&1"))
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
            self.assertFalse(os.path.exists(os.path.join(dest, "evals")))
            self.assertFalse(os.path.exists(os.path.join(dest, "tests")))

    def test_child_env_is_clean(self):
        os.environ["CLAUDE_CODE_SESSION_ID"] = "parent"
        try:
            env = agent.clean_env()
        finally:
            del os.environ["CLAUDE_CODE_SESSION_ID"]
        self.assertNotIn("CLAUDE_CODE_SESSION_ID", env)
        self.assertEqual(env["IS_SANDBOX"], "1")


if __name__ == "__main__":
    unittest.main()
