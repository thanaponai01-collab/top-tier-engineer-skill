#!/usr/bin/env python3
"""
The "How to work" section is copied into every skill so each stands alone.
This keeps the copies identical: edit one, edit all.

Run them all with `python -m unittest discover tests`.
"""
import glob, os, re, unittest

from _helpers import ROOT


class Philosophy(unittest.TestCase):
    def test_every_skill_carries_the_same_section(self):
        sections = {}
        for f in sorted(glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md"))):
            with open(f, encoding="utf-8") as fh:
                text = fh.read().replace("\r\n", "\n")
            m = re.search(r"^## How to work\n.*?(?=^## |\Z)", text, re.S | re.M)
            name = os.path.basename(os.path.dirname(f))
            self.assertIsNotNone(m, f"{name} has no '## How to work' section")
            sections[name] = m.group(0)
        self.assertTrue(sections, "no skills found")
        first = next(iter(sections.values()))
        drifted = [n for n, s in sections.items() if s != first]
        self.assertEqual(drifted, [], "How to work differs in these skills")


if __name__ == "__main__":
    unittest.main()
