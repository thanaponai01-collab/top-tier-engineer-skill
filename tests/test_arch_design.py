#!/usr/bin/env python3
"""
arch-design.py — the check behind docs/arch-design.md, the file an agent builds moves from.

Run them all with `python -m unittest discover tests`.
"""
import os, subprocess, tempfile, unittest

from _helpers import run


def write(root, rel, text=""):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def git(root, *args):
    return subprocess.run(["git", "-C", root, "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


HEAD = """# ARCH-DESIGN
- at: {sha}
- question: why does adding a report field touch six files?
- yardstick: add a report field; add an export format; change the tax rule
- status: open
- verdict: messy in places
"""

FINDING = """
## Finding 1: two owners for dates
- where: src/dates.py:2
- cost: 3 copies of the formatter
- badge: strong
- evidence: traced
"""

MOVE = """
## Move 1: one date formatter
- cost: 3 copies, 6 call sites
- pays: add a report field: 6 files -> 2
- files: src/dates.py:2, src/report.py:1
- owner: src/dates.py
- callers: src/report.py
- door: two-way
- proof: python -m unittest -> OK
- effort: S
- after: nothing
"""


def repo(tmp):
    git(tmp, "init", "-q")
    write(tmp, "src/dates.py", "import datetime\ndef fmt(d):\n    return d.isoformat()\n")
    write(tmp, "src/report.py", "from dates import fmt\n")
    git(tmp, "add", "-A")
    git(tmp, "commit", "-q", "-m", "init")
    return git(tmp, "rev-parse", "--short", "HEAD")


def doc(tmp, body, sha=None):
    write(tmp, "docs/arch-design.md", HEAD.format(sha=sha or repo(tmp)) + body)
    return os.path.join(tmp, "docs", "arch-design.md")


class Check(unittest.TestCase):
    def test_a_complete_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = doc(tmp, FINDING + MOVE)
            rc, out, _ = run("arch-design.py", "check", path)
            self.assertEqual(rc, 0, out)
            self.assertIn("ARCH: 1 moves", out)

    def test_a_tree_with_no_git_checks_paths_from_the_folder_above_docs(self):
        """Not a git repo (a fixture, a fresh export): docs/ is not the root, and there is no
        commit for `at:` to name, so staleness is skipped rather than reported as broken."""
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "src/dates.py", "import datetime\ndef fmt(d):\n    return d.isoformat()\n")
            write(tmp, "src/report.py", "from dates import fmt\n")
            write(tmp, "docs/arch-design.md", HEAD.format(sha="none") + FINDING + MOVE)
            rc, out, _ = run("arch-design.py", "check", os.path.join(tmp, "docs", "arch-design.md"))
            self.assertEqual(rc, 0, out)
            self.assertNotIn("STALE", out)

    def test_no_git_still_rejects_a_path_that_is_not_there(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "src/report.py", "from dates import fmt\n")           # dates.py is missing
            write(tmp, "docs/arch-design.md", HEAD.format(sha="none") + FINDING + MOVE)
            rc, out, _ = run("arch-design.py", "check", os.path.join(tmp, "docs", "arch-design.md"))
            self.assertEqual(rc, 1, out)
            self.assertIn("src/dates.py", out)

    def test_no_file_is_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, _, _ = run("arch-design.py", "check", os.path.join(tmp, "docs", "arch-design.md"))
            self.assertEqual(rc, 2)

    def test_a_move_missing_a_field_is_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = FINDING + MOVE.replace("- proof: python -m unittest -> OK\n", "")
            rc, out, _ = run("arch-design.py", "check", doc(tmp, body))
            self.assertEqual(rc, 1)
            self.assertIn("Move 1", out)
            self.assertIn("proof", out)

    def test_a_named_file_that_does_not_exist_is_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = FINDING + MOVE.replace("src/report.py:1", "src/gone.py:1")
            rc, out, _ = run("arch-design.py", "check", doc(tmp, body))
            self.assertEqual(rc, 1)
            self.assertIn("src/gone.py", out)

    def test_a_line_past_the_end_of_the_file_is_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = FINDING + MOVE.replace("src/dates.py:2,", "src/dates.py:99,")
            rc, out, _ = run("arch-design.py", "check", doc(tmp, body))
            self.assertEqual(rc, 1)
            self.assertIn("src/dates.py:99", out)

    def test_a_one_way_door_needs_a_recorded_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = FINDING + MOVE.replace("- door: two-way", "- door: one-way")
            rc, out, _ = run("arch-design.py", "check", doc(tmp, body))
            self.assertEqual(rc, 1)
            self.assertIn("confirmed", out)
            body = FINDING + MOVE.replace("- door: two-way", "- door: one-way, confirmed: user said go, 2026-09-26")
            rc, out, _ = run("arch-design.py", "check", doc(tmp, body))
            self.assertEqual(rc, 0, out)

    def test_after_must_name_a_move_that_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = FINDING + MOVE.replace("- after: nothing", "- after: 7")
            rc, out, _ = run("arch-design.py", "check", doc(tmp, body))
            self.assertEqual(rc, 1)
            self.assertIn("after", out)

    def test_a_strong_finding_needs_a_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = FINDING.replace("3 copies of the formatter", "messy") + MOVE
            rc, out, _ = run("arch-design.py", "check", doc(tmp, body))
            self.assertEqual(rc, 1)
            self.assertIn("Finding 1", out)


class Stale(unittest.TestCase):
    def test_a_change_to_a_named_file_after_the_pinned_commit_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = doc(tmp, FINDING + MOVE)
            write(tmp, "src/dates.py", "import datetime\ndef fmt(d):\n    return str(d)\n")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-q", "-m", "edit dates")
            rc, out, _ = run("arch-design.py", "check", path)
            self.assertEqual(rc, 1)
            self.assertIn("STALE", out)
            self.assertIn("src/dates.py", out)

    def test_a_change_elsewhere_is_not_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = doc(tmp, FINDING + MOVE)
            write(tmp, "src/other.py", "x = 1\n")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-q", "-m", "unrelated")
            rc, out, _ = run("arch-design.py", "check", path)
            self.assertEqual(rc, 0, out)

    def test_a_landed_file_is_never_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = doc(tmp, FINDING + MOVE)
            with open(path, encoding="utf-8") as fh:
                text = fh.read().replace("- status: open", "- status: landed")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            write(tmp, "src/dates.py", "import datetime\ndef fmt(d):\n    return str(d)\n")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-q", "-m", "the moves landed")
            rc, out, _ = run("arch-design.py", "check", path)
            self.assertEqual(rc, 0, out)


if __name__ == "__main__":
    unittest.main()
