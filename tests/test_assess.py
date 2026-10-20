"""1.16.0: --assess / --state-dir / VERIFY_STATE_DIR keep every helper write outside the checked repo,
so assessing a repo leaves its tree exactly as it was, and report still reads the state back.

Run with: python -m unittest discover tests
"""
import os, subprocess, tempfile, unittest
from pathlib import Path

from _helpers import run

REFUND = "def apply_refund(credit, amount):\n    return credit + amount\n"
TEST = ("import unittest\nfrom refund import apply_refund\n\n"
        "class T(unittest.TestCase):\n    def test_adds(self):\n"
        "        self.assertEqual(apply_refund(100, 50), 150)\n")


def project(root):
    Path(root, "refund.py").write_text(REFUND, encoding="utf-8")
    Path(root, "test_refund.py").write_text(TEST, encoding="utf-8")
    Path(root, "VERIFY.md").write_text("## Refunds\n- path: refund.py\n- test: `python -m unittest test_refund -q`\n"
                                       "- fail-signal: AssertionError\n", encoding="utf-8")


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, check=True).stdout


def git_project(root):
    project(root)
    git(root, "init", "-q")
    git(root, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init")


def listing(root):
    return sorted(str(p.relative_to(root)) for p in Path(root).rglob("*") if ".git" not in p.parts)


class Assess(unittest.TestCase):
    def test_assess_path_leaves_git_status_unchanged_and_report_reads_state(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as state:
            git_project(root)
            before = git(root, "status", "--porcelain", "--untracked-files=all")
            code, out, _ = run("verify.py", "run", root, "--state-dir", state)
            self.assertEqual(code, 0, out)
            code, out, _ = run("verify.py", "challenge", root, "--feature", "Refunds", "--auto",
                               "--state-dir", state)
            self.assertIn("CHALLENGE-AUTO", out)
            code, out, _ = run("verify.py", "report", root, "--state-dir", state)
            self.assertIn("VERIFY:", out)
            self.assertNotIn("No verification run recorded", out)
            if "NEXT" in out:  # a follow-up command must find the same state
                self.assertIn("--state-dir", out)
            self.assertEqual(git(root, "status", "--porcelain", "--untracked-files=all"), before)
            homes = os.listdir(state)
            self.assertEqual(len(homes), 1, homes)  # one folder for the repo; scratch copies kept theirs
            self.assertTrue(Path(state, homes[0], ".verify-state.json").is_file())
            # Without the option the state is somewhere else: this run has no memory of it.
            code, out, _ = run("verify.py", "report", root)
            self.assertIn("no run recorded", out)

    def test_assess_flag_uses_verify_state_dir_and_writes_nothing_into_a_plain_folder(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as state:
            project(root)  # no Git: the cache would otherwise land in .verify-state-cache/
            before = listing(root)
            old = os.environ.get("VERIFY_STATE_DIR")
            os.environ["VERIFY_STATE_DIR"] = state
            try:
                code, out, _ = run("verify.py", "run", root, "--assess")
                self.assertEqual(code, 0, out)
                code, out, _ = run("verify.py", "status", root, "--assess")
                self.assertNotIn("none", out.split("\n")[0], out)
            finally:
                if old is None:
                    os.environ.pop("VERIFY_STATE_DIR")
                else:
                    os.environ["VERIFY_STATE_DIR"] = old
            self.assertEqual(listing(root), before)
            self.assertTrue(os.listdir(state))

    def test_default_still_keeps_state_in_the_repo(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 0, out)
            self.assertTrue(Path(root, ".verify-state.json").is_file())

    def test_assess_and_state_dir_are_exclusive(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            code, _, err = run("verify.py", "run", root, "--assess", "--state-dir", root)
            self.assertEqual(code, 2)
            self.assertIn("not allowed with", err)


if __name__ == "__main__":
    unittest.main()
