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
    def seed_handoff(self, tmp):
        write(tmp, "AGENTS.md", "<!-- start-here -->\nintent: BRIEF.md\nwork: BUILD.md\n<!-- /start-here -->\n")
        write(tmp, "BRIEF.md", "# Goal\nExport invoices for accounting.\n")
        write(tmp, "BUILD.md", "## Next\nProve tenant-separated JSON.\n")

    def test_handoff_mode_rejects_empty_setup_without_changing_legacy_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run("context_budget.py", tmp)[0], 0)
            code, out, _ = run("context_budget.py", tmp, "--check-handoff")
            self.assertEqual(code, 1, out)
            self.assertIn("start-here", out)
            self.assertIn("BRIEF.md", out)

    def test_handoff_mode_checks_missing_included_requirements_and_next(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_handoff(tmp)
            write(tmp, "BRIEF.md", "# Goal\nAccounting export.\ninclude: brief/billing.md\n")
            write(tmp, "BUILD.md", "## Next\n\n## Done\nCSV worked.\n")
            code, out, _ = run("context_budget.py", tmp, "--check-handoff")
            self.assertEqual(code, 1, out)
            self.assertIn("brief/billing.md", out)
            self.assertIn("Next", out)

    def test_handoff_supports_existing_equivalent_documents_and_relative_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "AGENTS.md", "<!-- start-here -->\nintent: docs/product.md\nwork: notes/current.md\n<!-- /start-here -->\n")
            write(tmp, "docs/product.md", "# Goal\nAccounting.\n[Billing](billing.md)\n")
            write(tmp, "docs/billing.md", "Billing requirements.\n")
            write(tmp, "notes/current.md", "## Next\nVerify export.\n")
            code, out, _ = run("context_budget.py", tmp, "--check-handoff")
            self.assertEqual(code, 0, out)
            write(tmp, "docs/product.md", "# Goal\nAccounting.\n[Billing](missing.md)\n")
            code, out, _ = run("context_budget.py", tmp, "--check-handoff")
            self.assertEqual(code, 1, out)
            self.assertIn("missing.md", out)

    def test_handoff_rejects_malformed_block_and_empty_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_handoff(tmp)
            write(tmp, "AGENTS.md", "<!-- start-here -->\nintent: BRIEF.md\nwork: BUILD.md\n")
            write(tmp, "BRIEF.md", "# Goal\n## Decisions\n")
            code, out, _ = run("context_budget.py", tmp, "--check-handoff")
            self.assertEqual(code, 1, out)
            self.assertIn("markers", out)
            self.assertIn("empty", out)

    def test_unfinished_area_has_budget_and_remains_linked(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_handoff(tmp)
            write(tmp, "BUILD.md", "## Next\nVerify export.\ninclude: work/billing.md\n")
            write(tmp, "work/billing.md", lines(81, "- unresolved"))
            code, out, _ = run("context_budget.py", tmp, "--check-handoff")
            self.assertEqual(code, 1, out)
            self.assertIn("work/billing.md", out)

    def test_context_backlinks_do_not_break_a_valid_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_handoff(tmp)
            write(tmp, "BRIEF.md", "# Goal\nExport invoices.\n[Details](brief/billing.md)\n")
            write(tmp, "brief/billing.md", "Current billing requirements.\n[Goal](../BRIEF.md)\n")
            code, out, _ = run("context_budget.py", tmp, "--check-handoff")
            self.assertEqual(code, 0, out)

    def test_equivalent_work_document_is_budgeted(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_handoff(tmp)
            write(tmp, "AGENTS.md", "<!-- start-here -->\nintent: BRIEF.md\nwork: CURRENT.md\n<!-- /start-here -->\n")
            write(tmp, "CURRENT.md", "## Next\nVerify export.\n" + lines(80))
            code, out, _ = run("context_budget.py", tmp, "--check-handoff")
            self.assertEqual(code, 1, out)
            self.assertIn("CURRENT.md", out)
            self.assertIn("OVER", out)

    def test_outside_project_context_pointer_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.seed_handoff(tmp)
            write(tmp, "BRIEF.md", "# Goal\nExport invoices.\ninclude: ../outside.md\n")
            code, out, _ = run("context_budget.py", tmp, "--check-handoff")
            self.assertEqual(code, 1, out)
            self.assertIn("outside project", out)

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

    def test_active_area_decisions_are_measured_without_archiving_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "BRIEF.md", "include: brief/billing.md\n")
            write(tmp, "brief/billing.md", "## Decisions\n" + lines(26, "- active"))
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("brief/billing.md decisions", out)
            self.assertIn("split active decisions", out)

    def test_a_repo_with_no_notes_is_silent_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("context_budget.py", tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("no project notes", out)


if __name__ == "__main__":
    unittest.main()
