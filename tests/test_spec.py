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
    """The template with every slot filled by 'x': no wording of the term itself anywhere."""
    with open(TEMPLATE, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"\[\[fill:[^\]]*\]\]", "x", text)
    for marker, prose in [("acceptance", "tests/test_spec.py passes"),
                          ("evidence", "`python -m unittest`"),
                          ("verification", "`python -m unittest`")]:
        text = text.replace("<!-- %s -->x" % marker, "<!-- %s -->%s" % (marker, prose))
    return text


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

    def test_any_wording_passes_when_each_term_is_marked(self):
        text = filled_template()
        for phrase in ["end state is", "done when", "in scope", "must", "evidence is",
                       "accepted when", "verified by"]:
            self.assertNotIn(phrase, re.sub(r"<!--.*?-->", "", text, flags=re.S).lower())
        self.assertEqual(self.check_text(text)[0], 0)

    def test_each_gap_is_refused_and_all_are_listed_at_once(self):
        good = filled_template()
        for old in ["## Freedom", "<!-- invariants -->x", "<!-- evidence -->`python -m unittest`",
                    "<!-- verification -->`python -m unittest`", "tests/test_spec.py",
                    "<!-- escalation -->x"]:
            self.assertIn(old, good)
        broken = (good.replace("## Freedom", "## Latitude")
                      .replace("<!-- invariants -->x", "x")
                      .replace("<!-- evidence -->`python -m unittest`", "<!-- evidence -->it ran")
                      .replace("<!-- verification -->`python -m unittest`",
                               "<!-- verification -->the tests")
                      .replace("tests/test_spec.py", "tests/test_nowhere.py")
                      .replace("<!-- escalation -->x", "<!-- escalate -->x"))
        code, out = self.check_text(broken)
        self.assertEqual(code, 1)
        for needle in ["missing part: ## Freedom",
                       "Guardrails: nothing covers the invariants (put <!-- invariants -->",
                       "Guardrails: unknown marker <!-- escalate -->",
                       "Gates: evidence 'it ran",
                       "Output: verification names no `command`",
                       "tests/test_nowhere.py does not exist"]:
            self.assertIn(needle, out)

    def test_a_stage_missing_a_marker_and_an_empty_term_are_refused(self):
        good = filled_template()
        text = good.replace("<!-- postcondition -->x", "").replace("<!-- purpose -->x",
                                                                   "<!-- purpose -->")
        code, out = self.check_text(text)
        self.assertEqual(code, 1)
        self.assertIn("Gates: each stage needs all three markers", out)
        self.assertIn("Intent: <!-- purpose --> has no prose after it", out)

    def test_parts_out_of_order_are_refused(self):
        good = filled_template()
        head, rest = good.split("## Intent", 1)
        intent, after = rest.split("## Context", 1)
        code, out = self.check_text(head + "## Context" + after + "\n## Intent" + intent)
        self.assertEqual(code, 1)
        self.assertIn("parts out of order", out)

    def test_unmarked_prose_is_refused(self):
        prose = "\n".join(["# t", "## Intent", "The end state is x.", "## Context", "x",
                            "## Guardrails", "x", "## Freedom", "x", "## Gates", "x",
                            "## Output", "x"])
        code, out = self.check_text(prose)
        self.assertEqual(code, 1)
        self.assertIn("Intent: nothing covers the end state (put <!-- end state --> before", out)


if __name__ == "__main__":
    unittest.main()
