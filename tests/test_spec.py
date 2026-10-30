#!/usr/bin/env python3
"""
spec — a build starts from a brief that fills work/SPEC_TEMPLATE.md.

Run them all with `python -m unittest discover tests`.
"""
import os, re, subprocess, sys, tempfile, unittest

from _helpers import ROOT

CHECK = os.path.join(ROOT, "tools", "spec_check.py")
TEMPLATE = os.path.join(ROOT, "work", "SPEC_TEMPLATE.md")
# Skills that shipped before the template; every skill added after needs work/briefs/<skill>.md.
BEFORE_TEMPLATE = {"arch-design", "debug-protocol", "evolve-maintain", "feature-map",
                   "latent-audit", "perf-optimize", "safe-release", "structure-gate",
                   "threat-model", "verify-loop", "wire-check"}


def spec_check(*paths):
    p = subprocess.run([sys.executable, CHECK, *paths], capture_output=True, text=True,
                       encoding="utf-8")
    return p.returncode, p.stdout


def filled_template():
    with open(TEMPLATE, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"\[\[fill:[^\]]*\]\]", "x", text)
    return (text.replace("- Acceptance: x", "- Acceptance: tests/test_spec.py passes")
                .replace("- Verification: x", "- Verification: `python -m unittest`"))


class Spec(unittest.TestCase):
    def check_text(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "BRIEF.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            return spec_check(path)

    def test_brief_fills_the_template(self):
        code, out = spec_check(os.path.join(ROOT, "BRIEF.md"))
        self.assertEqual(code, 0, out)

    def test_every_new_skill_has_a_brief(self):
        skills = set(os.listdir(os.path.join(ROOT, "plugin", "skills")))
        for skill in sorted(skills - BEFORE_TEMPLATE):
            brief = os.path.join(ROOT, "work", "briefs", skill + ".md")
            self.assertTrue(os.path.exists(brief), "%s has no work/briefs/%s.md" % (skill, skill))
            code, out = spec_check(brief)
            self.assertEqual(code, 0, out)

    def test_template_is_refused_until_filled(self):
        code, out = spec_check(TEMPLATE)
        self.assertEqual(code, 1)
        self.assertIn("unfilled [[fill: ...]] slot", out)
        code, out = self.check_text(filled_template())
        self.assertEqual(code, 0, out)

    def test_each_gap_is_refused_and_all_are_listed_at_once(self):
        good = filled_template()
        broken = (good.replace("## 4. Freedom", "## 4. Latitude")
                      .replace("- Invariants: x", "- Invariants:")
                      .replace("| x | x | x | x |", "| x | x | x |  |")
                      .replace("`python -m unittest`", "run the tests")
                      .replace("tests/test_spec.py", "tests/test_nowhere.py"))
        code, out = self.check_text(broken)
        self.assertEqual(code, 1)
        for needle in ["missing section: ## 4. Freedom",
                       "Guardrails: empty field 'Invariants'",
                       "Gates: row 'x' leaves a cell empty",
                       "Verification names no `command`",
                       "tests/test_nowhere.py does not exist"]:
            self.assertIn(needle, out)

    def test_sections_out_of_order_are_refused(self):
        good = filled_template()
        head, rest = good.split("## 1. Intent", 1)
        intent, after = rest.split("## 2. Context", 1)
        code, out = self.check_text(head + "## 2. Context" + after + "\n## 1. Intent" + intent)
        self.assertEqual(code, 1)
        self.assertIn("sections out of order", out)


if __name__ == "__main__":
    unittest.main()
