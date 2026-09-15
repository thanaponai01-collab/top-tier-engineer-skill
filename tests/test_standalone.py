#!/usr/bin/env python3
"""
CLAUDE.md's other rules, held by a test: each skill names itself and leaves
"How to work" to PHILOSOPHY.md.

Run them all with `python -m unittest discover tests`.
"""
import glob, os, re, unittest

from _helpers import ROOT

SKILLS = {
    os.path.basename(os.path.dirname(f)): f
    for f in glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md"))
}


def read(f):
    with open(f, encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


class Standalone(unittest.TestCase):
    def test_frontmatter_names_the_folder(self):
        for name, f in SKILLS.items():
            m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", read(f))
            self.assertIsNotNone(m, f"{name}: frontmatter is not name + one-line description")
            self.assertEqual(m.group(1), name)

    def test_philosophy_lives_outside_skills(self):
        for name, f in SKILLS.items():
            self.assertNotIn("\n## How to work\n", read(f), f"{name}: How to work belongs in PHILOSOPHY.md")


if __name__ == "__main__":
    unittest.main()
