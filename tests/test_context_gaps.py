"""Regression checks for the fresh-session gaps measured in docs/context-gaps.md (G1-G9),
and for the foundation front door (/project-foundation) that follows /project-setup.

Run everything with: python -m unittest discover tests
"""
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def skill(name):
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def frontmatter(text):
    return text.split("---", 2)[1]


start_here = load("start_here_hook", ROOT / "tools" / "start-here-hook.py")
front_door = load("front_door", ROOT / "tools" / "front-door.py")


def run_state(status="active", journal=None, proofs=None):
    return {"status": status, "proofs": proofs or {}, "journal": journal or {},
            "contract": {"goal": "g", "stages": [{"id": "diagnose"}, {"id": "prove"}]}}


class G1DrivenRunAtStartup(unittest.TestCase):
    def repo(self, state):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name)
        if state is not None:
            (path / "RUN.json").write_text(state if isinstance(state, str) else json.dumps(state),
                                           encoding="utf-8")
        return path

    def test_active_run_with_unknown_action_is_announced(self):
        repo = self.repo(run_state(journal={"deploy": {"result": "unknown"}},
                                   proofs={"diagnose": {}}))
        text = start_here.compact_summary(str(repo))
        self.assertIn("Driven run: active", text)
        self.assertIn("next: prove", text)
        self.assertIn("unresolved actions: 1", text)
        self.assertIn("reconcile", text)

    def test_blocked_run_is_announced(self):
        repo = self.repo(run_state(status="blocked"))
        self.assertIn("Driven run: blocked", start_here.compact_summary(str(repo)))

    def test_complete_run_and_no_run_stay_silent(self):
        self.assertNotIn("Driven run", start_here.compact_summary(str(self.repo(run_state("complete")))))
        self.assertNotIn("Driven run", start_here.compact_summary(str(self.repo(None))))

    def test_malformed_run_fails_open_with_a_pointer(self):
        text = start_here.compact_summary(str(self.repo("{not json")))
        self.assertIn("Driven run: unreadable", text)

    def test_front_door_shows_the_run_in_a_project_never_set_up(self):
        repo = self.repo(run_state())
        (repo / ".git").mkdir()
        self.assertIn("Driven run: active", front_door.front_door(str(repo)))


class G2PlansReachTheWorkDocument(unittest.TestCase):
    def test_plan_work_links_plan_from_work_document(self):
        self.assertIn("include: PLAN.md", skill("plan-work"))

    def test_agent_design_links_its_contract_from_work_document(self):
        self.assertIn("include: docs/agent-design.md", skill("agent-design"))


class G3NoMojibake(unittest.TestCase):
    def test_no_double_encoded_utf8_in_skills(self):
        bad = [str(p) for p in SKILLS.rglob("*.md")
               if b"\xc3\xa2\xe2\x80" in p.read_bytes() or b"\xc3\x82\xc2\xb7" in p.read_bytes()]
        self.assertEqual(bad, [])


class G4DescriptionsSayWhen(unittest.TestCase):
    def test_every_model_invocable_skill_has_a_trigger(self):
        missing = []
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            fm = frontmatter(path.read_text(encoding="utf-8"))
            if "disable-model-invocation: true" in fm:
                continue
            if not re.search(r"\bUse (for|when|at|before|after|on)\b", fm):
                missing.append(path.parent.name)
        self.assertEqual(missing, [])


class G5SharedTextLivesOnce(unittest.TestCase):
    def test_memory_paragraph_is_not_copied_into_skills(self):
        copies = [p.parent.name for p in SKILLS.glob("*/SKILL.md")
                  if "Project memory: retrieve missing facts" in p.read_text(encoding="utf-8")]
        self.assertEqual(copies, [])

    def test_one_evidence_label_definition(self):
        variants = set()
        for path in SKILLS.glob("*/SKILL.md"):
            text = path.read_text(encoding="utf-8")
            match = re.search(r"^\*Evidence labels:.*?\*$", text, re.M | re.S)
            if match:
                variants.add(" ".join(match.group(0).split()))
        self.assertEqual(len(variants), 1, variants)


class G6ContextRoleTable(unittest.TestCase):
    def test_memory_reference_has_one_role_table(self):
        text = (SKILLS / "project-context" / "references" / "memory.md").read_text(encoding="utf-8")
        self.assertIn("## Context roles", text)
        for name in ("BRIEF.md", "BUILD.md", "RUN.json", "PLAN.md", "VERIFY.md", "FEATURES.md",
                     "WHY.md", "docs/architecture.md", "docs/commands.md", "docs/agent-design.md"):
            self.assertIn(name, text, name)

    def test_recall_reads_the_table_instead_of_its_own_list(self):
        text = skill("recall")
        self.assertIn("Context roles", text)
        self.assertNotIn("`docs/arch-design.md`,\n  `docs/architecture.md`, `WHY.md`", text)


class G7CodeHistoryLeavesTheReason(unittest.TestCase):
    def test_why_entry_is_unconditional_for_multi_record_or_expired(self):
        text = skill("code-history")
        self.assertNotIn("When the answer took real digging", text)
        self.assertRegex(text, r"more than one record")
        self.assertRegex(text, r"(?i)expired")


class G8ScratchCheckout(unittest.TestCase):
    def test_scrutinize_names_the_worktree_command(self):
        text = skill("scrutinize")
        self.assertIn("git worktree add", text)
        self.assertRegex(text, r"(?i)never .{0,40}checkout")


class G9WritesStayInTheRepo(unittest.TestCase):
    def test_context_writing_skills_name_the_repository_root(self):
        for name in ("arch-map", "issue-handoff", "feature-map", "code-history"):
            self.assertIn("inside the repository root", skill(name), name)


class FoundationFrontDoor(unittest.TestCase):
    def test_project_foundation_is_a_manual_skill(self):
        text = skill("project-foundation")
        self.assertIn("name: project-foundation", text)
        self.assertIn("disable-model-invocation: true", text)

    def test_setup_and_cold_projects_point_to_it(self):
        self.assertIn("/project-foundation", skill("project-setup"))
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        (Path(tmp.name) / ".git").mkdir()
        self.assertIn("project-foundation", front_door.setup_line(tmp.name))

    def test_drive_and_onboard_load_it(self):
        for name in ("drive", "onboard-system"):
            self.assertIn("project-foundation", skill(name), name)
            self.assertNotIn("references/prepare-foundation.md", skill(name), name)

    def test_list_prints_every_category_with_its_state(self):
        script = SKILLS / "project-foundation" / "scripts" / "foundation.py"
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        (Path(tmp.name) / "BRIEF.md").write_text("# Brief\n", encoding="utf-8")
        out = subprocess.run([sys.executable, str(script), "--repo", tmp.name, "list"],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        for role in ("intent", "work", "features", "verify", "architecture", "commands", "memory"):
            self.assertRegex(out.stdout, rf"(?m)^\| {role} \|", role)
        self.assertRegex(out.stdout, r"(?m)^\| intent \| BRIEF.md \| present")
        self.assertRegex(out.stdout, r"(?m)^\| work \| BUILD.md \| missing")


if __name__ == "__main__":
    unittest.main()
