#!/usr/bin/env python3
"""
CLAUDE.md's other rules, held by a test: each skill names itself, mentions no
other skill, and keeps "How to work" as its last section.

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

    def test_no_skill_mentions_another(self):
        for name, f in SKILLS.items():
            body = read(f).split("\n---\n", 1)[1]
            others = [o for o in SKILLS if o != name and o in body]
            self.assertEqual(others, [], f"{name} references other skills")

    def test_how_to_work_is_last(self):
        for name, f in SKILLS.items():
            after = read(f).split("\n## How to work\n", 1)[1]
            self.assertNotRegex(after, r"(?m)^## ", f"{name}: a section follows How to work")


if __name__ == "__main__":
    unittest.main()
