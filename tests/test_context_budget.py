#!/usr/bin/env python3
"""
context_budget.py — the line budgets that keep a fresh session's reading short (recall).

Run them all with `python -m unittest discover tests`.
"""
import os, tempfile, unittest

from _helpers import run


def write(root, rel, text):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def lines(n, prefix="line"):
    return "".join(f"{prefix} {i}\n" for i in range(n))


class Budget(unittest.TestCase):
    def test_notes_within_budget_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "BRIEF.md", "# Brief\n## Decisions\n- 2026-10-09 · JSON only\n")
            write(tmp, "BUILD.md", lines(20))
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("0 over budget", out)

    def test_an_over_budget_file_fails_and_names_its_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "BUILD.md", lines(81))
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("OVER", out)
            self.assertIn("BUILD.archive.md", out)

    def test_too_many_decisions_fail_even_in_a_short_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "BRIEF.md", "## Decisions\n" + lines(26, "- d") + "## Not building\n- x\n")
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("BRIEF.md decisions", out)
            self.assertIn("BRIEF.archive.md", out)

    def test_only_the_start_here_block_counts_not_the_whole_instruction_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            block = "<!-- start-here -->\n" + lines(10) + "<!-- /start-here -->\n"
            write(tmp, "CLAUDE.md", lines(200, "house rule") + block)
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("CLAUDE.md start-here", out)
            write(tmp, "CLAUDE.md", "<!-- start-here -->\n" + lines(31) + "<!-- /start-here -->\n")
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 1, out)

    def test_an_included_area_file_has_its_own_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "FEATURES.md", "# Features\n- include: `features/billing.md`\n- include: features/auth.md\n")
            write(tmp, "features/billing.md", lines(151))
            write(tmp, "features/auth.md", lines(10))
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("features/billing.md", out)
            self.assertIn("features/auth.md", out)

    def test_archives_are_never_measured(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "BUILD.archive.md", lines(5000))
            write(tmp, "BUILD.md", lines(5))
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 0, out)
            self.assertNotIn("archive.md ", out)

    def test_a_repo_with_no_notes_is_silent_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("no project notes", out)


if __name__ == "__main__":
    unittest.main()
