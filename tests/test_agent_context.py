#!/usr/bin/env python3
"""
A fresh agent in this repo should find what the plugin is, where each fact lives and what is next,
without reading the same list twice. These checks hold the repo to that.
"""
import re
import unittest
from pathlib import Path

from _helpers import ROOT

R = Path(ROOT)


def text(rel):
    return (R / rel).read_text(encoding="utf-8")


def words(rel):
    return len(text(rel).split())


class FreshAgentEntry(unittest.TestCase):
    def test_agents_md_points_non_claude_agents_at_the_same_rules(self):
        t = text("AGENTS.md")
        self.assertLessEqual(len(t.splitlines()), 12)
        self.assertIn("CLAUDE.md", t)

    def test_brief_says_what_the_whole_repo_is(self):
        t = text("BRIEF.md")
        self.assertIn("## What this repo is", t)
        for anchor in ("plugin/", "tools/catalog.py", "evals/"):
            self.assertIn(anchor, t, f"BRIEF.md never says where {anchor} fits")
        self.assertLessEqual(len(t.splitlines()), 120)

    def test_build_is_current_state_not_release_history(self):
        t = text("BUILD.md")
        self.assertIn("## Next", t)
        self.assertIn("CHANGELOG.md", t)
        self.assertLessEqual(len(t.splitlines()), 40)


class OneHomePerList(unittest.TestCase):
    def test_flows_table_has_one_home(self):
        header = "| Goal | Find | Change | Prove | Ship |"
        homes = [p for p in ("README.md", "plugin/skills/pick-skill/SKILL.md", "CATALOG.md") if header in text(p)]
        self.assertEqual(homes, ["plugin/skills/pick-skill/SKILL.md"])

    def test_readme_skill_table_is_generated(self):
        t = text("README.md")
        self.assertIn("<!-- skills:start", t)
        self.assertIn("<!-- skills:end -->", t)

    def test_hand_edited_readme_table_is_caught(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("catalog", R / "tools" / "catalog.py")
        cat = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cat)
        skills = cat.load_skills()
        fresh = cat.expected_files(skills)[cat.README]
        self.assertEqual(cat.read(cat.README), fresh)
        self.assertNotEqual(fresh.replace("| `recall` |", "| `recall` x |"), fresh)

    def test_readme_stays_short_enough_to_read(self):
        self.assertLessEqual(words("README.md"), 2000)


class MergeAnalysis(unittest.TestCase):
    def test_merge_candidates_are_recorded_with_a_verdict(self):
        t = text("docs/merge-proposals.md")
        for name in ("drive-overnight", "project-setup", "agent-evals", "senior-review", "recall"):
            self.assertIn(name, t)
        self.assertRegex(t, r"(?i)parked")
        self.assertTrue(re.search(r"(?m)^\| .*\| (merge|keep|park)", t))


if __name__ == "__main__":
    unittest.main()
