#!/usr/bin/env python3
"""
change-map.py — the git-history reading behind arch-design.

Run them all with `python -m unittest discover tests`.
"""
import json, os, subprocess, tempfile, unittest

from _helpers import run


class ChangeMap(unittest.TestCase):
    """Planted history: web/views.py and jobs/export.py change together three
    times with no import between them (hidden coupling); billing/tax.py only
    ever changes alone (the decoy); one 40-file reformat commit must be skipped,
    not counted as coupling."""

    def _repo(self, tmp):
        def git(*a):
            subprocess.run(["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t",
                            *a], check=True, capture_output=True)

        def commit(files, msg):
            for f in files:
                p = os.path.join(tmp, f)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "a", encoding="utf-8") as fh:
                    fh.write(msg + "\n")
            git("add", "-A")
            git("commit", "-q", "-m", msg)

        git("init", "-q")
        for i in range(3):
            commit(["web/views.py", "jobs/export.py"], f"date format {i}")
            commit(["billing/tax.py"], f"tax rule {i}")
        commit([f"vendor/f{i}.py" for i in range(40)] + ["web/views.py", "billing/tax.py"], "reformat")

    def test_finds_the_coupled_pair_and_not_the_decoy(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp)
            code, out, err = run("change-map.py", tmp, "--depth", "1", "--json")
            self.assertEqual(code, 0, err)
            r = json.loads(out.split("\nCHANGE:")[0])
            pairs = {(c["a"], c["b"]) for c in r["coupled"]}
            self.assertEqual(pairs, {("jobs/export.py", "web/views.py")})
            self.assertEqual(r["commits_skipped_bulk"], 1)
            self.assertEqual(r["spread_p90"], 2)

    def test_no_history_says_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("change-map.py", tmp)
            self.assertEqual(code, 2)
            self.assertIn("CHANGE: blocked", out)


if __name__ == "__main__":
    unittest.main()
