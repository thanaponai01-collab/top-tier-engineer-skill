#!/usr/bin/env python3
"""
CLAUDE.md's other rules, held by a test: each skill names itself, leaves
"How to work" to PHILOSOPHY.md, and survives being read on its own.

The last part is what most of this file is about. The README invites people to
copy a single SKILL.md into another agent, so anything a skill relies on from
outside itself — a word defined elsewhere, another skill that finishes the job —
is a promise that breaks the moment the file travels alone.

Run them all with `python -m unittest discover tests`.
"""
import glob, os, re, unittest

from _helpers import ROOT

SKILLS = {
    os.path.basename(os.path.dirname(f)): f
    for f in glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md"))
}

# The gloss every skill must carry if it labels evidence at all. Checked by a
# stable fragment so re-wrapping the line does not break the test.
GLOSS = "**proven** = you ran it"

# Handoffs where the work stops or disappears if the named skill is absent.
# Each one has to state its own fallback in the paragraph that names it.
LOAD_BEARING = [
    ("arch-design", "arch-map"),
    ("arch-design", "latent-audit"),
    ("evolve-maintain", "debug-protocol"),
    ("evolve-maintain", "build-discipline"),
    ("evolve-maintain", "safe-release"),
    ("evolve-maintain", "latent-audit"),
    ("perf-optimize", "safe-release"),
]
FALLBACK_MARKERS = ("available", "fallback", "without it")


def read(f):
    with open(f, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def body(text):
    """Everything after the frontmatter."""
    return text.split("---\n", 2)[-1]


class Standalone(unittest.TestCase):
    def test_frontmatter_names_the_folder(self):
        for name, f in SKILLS.items():
            m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", read(f))
            self.assertIsNotNone(m, f"{name}: frontmatter is not name + one-line description")
            self.assertEqual(m.group(1), name)

    def test_philosophy_lives_outside_skills(self):
        for name, f in SKILLS.items():
            self.assertNotIn("\n## How to work\n", read(f), f"{name}: How to work belongs in PHILOSOPHY.md")

    def test_every_skill_carries_a_test_line(self):
        """An instruction nobody can check is one an agent claims for free."""
        for name, f in SKILLS.items():
            self.assertRegex(
                read(f), r"(?m)^\*Test:\*",
                f"{name}: no *Test:* line — nothing in this skill states how you would know it was "
                f"actually done",
            )

    def test_evidence_labels_are_defined_where_they_are_used(self):
        """proven / traced / suspected is this repo's notation, not English."""
        for name, f in SKILLS.items():
            text = read(f)
            if re.search(r"\btraced\b|\bsuspected\b", text) and GLOSS not in text:
                self.fail(
                    f"{name}: labels evidence but never defines the labels. Copied into another "
                    f"agent, that agent invents its own meaning — usually collapsing traced into "
                    f"proven, which is the failure the scale exists to stop."
                )

    def test_a_skill_that_does_not_label_evidence_carries_no_gloss(self):
        """The gloss is for skills that use it; elsewhere it is noise."""
        for name, f in SKILLS.items():
            text = read(f)
            if GLOSS in text:
                self.assertRegex(
                    text, r"\btraced\b|\bsuspected\b",
                    f"{name}: defines the evidence labels but never uses them",
                )

    def test_cross_skill_references_resolve(self):
        """A renamed skill must not leave a pointer to a skill that no longer exists."""
        for name, f in SKILLS.items():
            for token in set(re.findall(r"`([a-z][a-z0-9]*-[a-z0-9-]+)`", read(f))):
                self.assertIn(
                    token, SKILLS,
                    f"{name}: names `{token}`, which is not a skill in this repo",
                )

    def test_load_bearing_handoffs_state_a_fallback(self):
        for name, dependency in LOAD_BEARING:
            paragraphs = [p for p in body(read(SKILLS[name])).split("\n\n") if f"`{dependency}`" in p]
            self.assertTrue(paragraphs, f"{name}: no longer mentions `{dependency}` — update LOAD_BEARING")
            self.assertTrue(
                any(m in p.lower() for p in paragraphs for m in FALLBACK_MARKERS),
                f"{name}: hands work to `{dependency}` with no fallback. An agent without that "
                f"skill loaded finishes the analysis, announces the handoff, and produces nothing.",
            )

    def test_readme_lists_every_skill(self):
        readme = read(os.path.join(ROOT, "README.md"))
        for name in SKILLS:
            self.assertIn(name, readme, f"{name}: exists but the README never mentions it")


if __name__ == "__main__":
    unittest.main()
