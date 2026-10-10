#!/usr/bin/env python3
"""
tools/catalog.py keeps every list of skills in step with skills/. These tests hold the repo to it
and show the check fails when a copy drifts.

Run them all with `python -m unittest discover tests`.
"""
import importlib.util
from pathlib import Path
import unittest

from _helpers import ROOT

_spec = importlib.util.spec_from_file_location("catalog", Path(ROOT) / "tools" / "catalog.py")
catalog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(catalog)


class Catalog(unittest.TestCase):
    def test_every_copy_is_current(self):
        found = catalog.problems(catalog.load_skills())
        self.assertEqual(found, [], "run python tools/catalog.py --write, then fix what remains")

    def test_card_names_every_skill_once(self):
        skills = catalog.load_skills()
        card = catalog.card_text(skills)
        for s in skills:
            self.assertEqual(card.count(f"{s['name']}` "), 1, s["name"])

    def test_manual_skills_appear_as_slash_commands(self):
        skills = catalog.load_skills()
        card = catalog.card_text(skills)
        for s in skills:
            if s["manual"]:
                self.assertIn(f"`/top-tier-engineer:{s['name']}`", card, s["name"])

    def test_a_new_skill_nobody_listed_is_caught(self):
        skills = catalog.load_skills()
        ghost = dict(skills[0], name="ghost-skill", dir="ghost-skill")
        found = "\n".join(catalog.problems(skills + [ghost]))
        self.assertIn("CATALOG.md: stale", found)
        self.assertIn("plugin.json: stale", found)
        self.assertIn("table has no row for ghost-skill", found)
        self.assertIn("never names `ghost-skill`", found)

    def test_a_folder_and_name_mismatch_is_caught(self):
        skills = catalog.load_skills()
        skills[0] = dict(skills[0], dir="renamed-folder")
        self.assertTrue(any("frontmatter name is" in p for p in catalog.problems(skills)))

    def test_a_long_description_is_caught(self):
        skills = catalog.load_skills()
        i = next(i for i, s in enumerate(skills) if not s["manual"])
        skills[i] = dict(skills[i], description="x" * (catalog.DESC_MAX + 1))
        self.assertTrue(any("cap 160" in p for p in catalog.problems(skills)))

    def test_a_listing_over_budget_is_caught(self):
        skills = catalog.load_skills()
        extra = [dict(skills[0], manual=False, description="x" * 150, name=f"pad-{i}", dir=f"pad-{i}")
                 for i in range(5)]
        self.assertTrue(any("skill listing is" in p for p in catalog.problems(skills + extra)))

    def test_manual_skills_cost_nothing_in_the_listing(self):
        skills = catalog.load_skills()
        manual = [dict(skills[0], manual=True, description="x" * 999, name="m", dir="m")]
        self.assertEqual(catalog.listing_chars(skills + manual), catalog.listing_chars(skills))

    def test_bad_frontmatter_is_named(self):
        with self.assertRaisesRegex(ValueError, "no stage"):
            catalog.frontmatter('---\nname: x\ndescription: y\nmetadata:\n  card: "z"\n---\n')
        with self.assertRaisesRegex(ValueError, "unknown stage"):
            catalog.frontmatter('---\nname: x\ndescription: y\nmetadata:\n'
                                '  stage: nope\n  card: "z"\n---\n')

    def test_number_words(self):
        self.assertEqual([catalog.number_word(n) for n in (7, 19, 20, 33, 40)],
                         ["Seven", "Nineteen", "Twenty", "Thirty-three", "Forty"])

    def test_count_rewrite_keeps_the_adjective(self):
        self.assertEqual(catalog.with_count("Twenty-five independent engineering skills, x", 33),
                         "Thirty-three independent engineering skills, x")


if __name__ == "__main__":
    unittest.main()
