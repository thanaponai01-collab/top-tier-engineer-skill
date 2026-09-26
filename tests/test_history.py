#!/usr/bin/env python3
"""
history.py — the git-history reading behind code-history.

Run them all with `python -m unittest discover tests`.
"""
import json, os, subprocess, tempfile, unittest

from _helpers import run


class History(unittest.TestCase):
    """Planted history for cache.py: added with a stated reason, TTL tuned after
    an incident (#12), that change reverted, then a plain fix. other.py only
    exists so a symbol search has something to not match."""

    def _repo(self, tmp):
        def git(*a):
            subprocess.run(["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t",
                            *a], check=True, capture_output=True)

        def commit(name, text, msg):
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(text)
            git("add", "-A")
            git("commit", "-q", "-m", msg)

        git("init", "-q")
        commit("cache.py", "TTL = 300\ndef get_user(): pass\n",
               "add user cache\n\nBecause the profile page hit the db 40x per view.")
        commit("other.py", "x = 1\n", "unrelated")
        commit("cache.py", "TTL = 60\ndef get_user(): pass\n",
               "shorten TTL, fixes #12\n\nStale profiles caused the March incident.")
        commit("cache.py", "TTL = 300\ndef get_user(): pass\n",
               'Revert "shorten TTL, fixes #12"\n\nBroke billing (PROJ-45).')
        commit("cache.py", "TTL = 300\ndef get_user(): return 1\n", "fix get_user")

    def _json(self, *args):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            code, out, err = run("history.py", tmp, *args, "--json")
            self.assertEqual(code, 0, err)
            return json.loads(out)

    def test_file_history_finds_intro_reason_refs_and_revert(self):
        d = self._json("--file", "cache.py")
        self.assertEqual(len(d["commits"]), 4)
        self.assertEqual(d["introduced"]["subject"], "add user cache")
        self.assertIn("40x per view", d["introduced"]["body"])
        self.assertEqual(d["reverts"], 1)
        self.assertEqual(d["refs"], ["#12", "PROJ-45"])

    def test_symbol_search_finds_only_commits_that_changed_it(self):
        d = self._json("--symbol", "TTL")
        subjects = [c["subject"] for c in d["commits"]]
        self.assertNotIn("unrelated", subjects)
        self.assertNotIn("fix get_user", subjects)
        self.assertEqual(len(subjects), 3)

    def test_line_range_history(self):
        d = self._json("--lines", "cache.py:1,1")
        self.assertEqual(len(d["commits"]), 3)

    def test_summary_line_names_the_only_source_it_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            code, out, _ = run("history.py", tmp, "--file", "cache.py")
            self.assertEqual(code, 0)
            last = out.strip().splitlines()[-1]
            self.assertTrue(last.startswith("HISTORY: 4 commits"), last)
            self.assertIn("1 reverts", last)
            self.assertIn("sources: git only", last)

    def test_no_history_says_so_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            code, out, _ = run("history.py", tmp, "--file", "nope.py")
            self.assertEqual(code, 1)
            self.assertIn("no history", out.lower())

    def test_not_a_repo_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run("history.py", tmp, "--file", "a.py")
            self.assertEqual(code, 2)
            self.assertIn("not a git repo", err.lower())


if __name__ == "__main__":
    unittest.main()
