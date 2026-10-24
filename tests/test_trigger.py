#!/usr/bin/env python3
"""
The trigger eval, held by a test.

trigger.py decides from a transcript whether verify-loop fired and whether the try was isolated.
If either reading is wrong, every description tuned against it is tuned against noise, so both
are checked here on hand-built streams, along with the cases file and the description swap.
"""
import json, os, sys, unittest

from _helpers import ROOT

sys.path.insert(0, os.path.join(ROOT, "evals"))

import agent  # noqa: E402
import trigger  # noqa: E402


def stream(*tools, init=None):
    """stream-json lines: an init event, one assistant message per tool call, a result."""
    lines = [json.dumps(init or {"type": "system", "subtype": "init", "plugins": [
        {"name": "verify-loop", "path": "/x/plugin"}, {"name": "cc-plugin-telemetry", "path": "builtin"}],
        "skills": ["verify-loop:verify-loop", "verify", "debug"], "mcp_servers": []})]
    for i, (name, inp) in enumerate(tools):
        lines.append(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": f"t{i}", "name": name, "input": inp}]}}))
    lines.append(json.dumps({"type": "result", "total_cost_usd": 0.05, "num_turns": 2}))
    return lines


class Detection(unittest.TestCase):
    def score(self, *tools):
        return trigger.score_try(agent.parse_stream(stream(*tools)))

    def test_skill_call_fires(self):
        s = self.score(("Glob", {"pattern": "*"}), ("Skill", {"skill": "verify-loop:verify-loop"}))
        self.assertEqual((s["fired"], s["fired_at"]), (True, 2))

    def test_bundled_verify_is_a_competitor_not_a_fire(self):
        s = self.score(("Skill", {"skill": "verify"}))
        self.assertFalse(s["fired"])
        self.assertEqual(s["other_skills"], ["verify"])

    def test_running_tests_is_quiet(self):
        self.assertFalse(self.score(("Bash", {"command": "python -m unittest discover tests"}))["fired"])


class Isolation(unittest.TestCase):
    def test_builtins_and_this_plugin_are_clean(self):
        init = trigger.init_event(stream())
        self.assertEqual(trigger.leaks(init, {"caveman"}, 0), [])

    def test_each_leak_is_named(self):
        init = {"plugins": [{"name": "other", "path": "/p"}], "mcp_servers": [{"name": "drive"}],
                "skills": ["caveman", "mattpocock-skills:tdd", "verify"]}
        found = " ".join(trigger.leaks(init, {"caveman"}, 12))
        for word in ("plugin other", "user skill caveman", "mattpocock-skills:tdd", "mcp drive", "CLAUDE.md"):
            self.assertIn(word, found)

    def test_missing_init_is_not_clean(self):
        self.assertTrue(trigger.leaks({}, set(), 0))


class Scoring(unittest.TestCase):
    def test_leaked_tries_are_dropped_and_counted(self):
        cases = [{"id": "a", "fire": True, "split": "train"}, {"id": "b", "fire": False, "split": "test"}]
        base = {"other_skills": [], "error": None}
        tries = [dict(base, id="a", fired=True, leaks=[]), dict(base, id="a", fired=False, leaks=[]),
                 dict(base, id="b", fired=True, leaks=[]), dict(base, id="b", fired=True, leaks=["mcp x"])]
        s = trigger.summarize(tries, cases)
        self.assertEqual(s["invalid"], 1)
        self.assertEqual(s["splits"]["train"]["fired_when_wanted"], "1/2")
        self.assertEqual(s["splits"]["test"]["fired_when_not"], "1/1")
        self.assertEqual(s["splits"]["all"]["right"], "1/3")


class Cases(unittest.TestCase):
    def test_every_split_has_both_answers_and_prompts_are_unique(self):
        cases = trigger.load_cases()
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        self.assertEqual(len({c["prompt"] for c in cases}), len(cases))
        for split in ("train", "test"):
            wants = {c["fire"] for c in cases if c["split"] == split}
            self.assertEqual(wants, {True, False}, split)

    def test_fixture_has_a_change_to_verify(self):
        work = trigger.make_workdir()
        try:
            import subprocess
            diff = subprocess.run(["git", "diff", "--stat"], cwd=work, capture_output=True, text=True).stdout
            self.assertIn("pricing.py", diff)
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)


class Description(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "plugin", trigger.SKILL_FILE), encoding="utf-8") as fh:
            self.text = fh.read()

    def test_swap_replaces_only_the_description(self):
        new = trigger.set_description(self.text, "Use when the user asks for proof.  Second  line.")
        self.assertEqual(trigger.read_description(new), "Use when the user asks for proof. Second line.")
        self.assertEqual(new.split("metadata:", 1)[1], self.text.split("metadata:", 1)[1])
        self.assertIn("name: verify-loop", new)

    def test_live_description_is_the_measured_one(self):
        """A description edit must be re-scored: run evals/trigger.py, then update measured.json."""
        with open(os.path.join(ROOT, "evals", "trigger", "measured.json"), encoding="utf-8") as fh:
            measured = json.load(fh)
        self.assertEqual(trigger.read_description(self.text), measured["description"],
                         "SKILL.md description changed since the last trigger eval")

    def test_live_description_reads(self):
        live = trigger.read_description(self.text)
        self.assertGreater(len(live), 50)
        self.assertNotIn("metadata", live)
        self.assertNotIn(">-", live)


if __name__ == "__main__":
    unittest.main()
