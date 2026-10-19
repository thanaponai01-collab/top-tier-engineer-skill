"""Maintain mode: the read-only audit says what a pass must map, re-prove, fix or re-drive."""
import json, os, subprocess, tempfile, unittest

from _helpers import run

CHECK = "python check.py"
SKILL = """---
name: verify
description: >-
  Drive the thing.
---

# Verify the thing

Checks live in [VERIFY.md](../../../VERIFY.md).

## Launch
python src/app.py
## Doctor
none
## Drive
python check.py
## Evidence
.verify-evidence/
## Cleanup
nothing
## Helpers
none
## Verdict
verify.py report
"""
FEATURE = """# Thing

The thing works.

verify-section: Thing

## Sub-features
- `thing` it works.
## How to get to it (user POV)
- run it.
## Driving it with python
- `python check.py`
## Gotchas
- none
"""


def write(root, rel, text=""):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def git(root, *args):
    return subprocess.run(["git", "-C", root, "-c", "user.email=t@t", "-c", "user.name=t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def audit(root, *extra):
    code, out, _ = run("verify.py", "maintain", root, "--json", *extra)
    data = json.loads(out)
    return code, data, {r["feature"]: r for r in data.get("features", [])}


class Maintain(unittest.TestCase):
    def repo(self, tmp):
        write(tmp, "src/app.py", "VALUE = 42\n")
        write(tmp, "check.py", "import os, sys\nsys.exit(0 if os.path.exists('ok.flag') else "
                               "(print('expected ok.flag present') or 1))\n")
        write(tmp, "VERIFY.md", f"## Thing\n- path: src/\n- test: `{CHECK}`\n"
                                "- fail-signal: expected ok.flag present\n- fail-proof: removed ok.flag, went red\n")
        write(tmp, ".gitignore", ".verify-state.json\nok.flag\n")
        write(tmp, ".claude/skills/verify/SKILL.md", SKILL)
        write(tmp, ".claude/skills/verify/features/README.md", "# Map\n\n- [Thing](./thing.md)\n")
        write(tmp, ".claude/skills/verify/features/thing.md", FEATURE)
        git(tmp, "init", "-q")
        git(tmp, "add", "-A")
        git(tmp, "commit", "-qm", "skill")
        sha = git(tmp, "rev-parse", "--short", "HEAD")
        write(tmp, ".claude/skills/verify/features/README.md",
              f"# Map\n\nlast-maintained: {sha}\n\n- [Thing](./thing.md)\n")
        git(tmp, "commit", "-qam", "maintained")
        run("verify.py", "run", tmp)                     # rejection receipt
        write(tmp, "ok.flag")
        run("verify.py", "baseline", tmp)
        run("verify.py", "run", tmp, "--strict")
        return sha

    def test_no_skill_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, data, _ = audit(tmp)
            self.assertEqual((code, data["outcome"]), (2, "blocked"))
            self.assertIn("MAINTAIN: blocked", run("verify.py", "maintain", tmp)[1])

    def test_proven_unchanged_feature_only_needs_its_live_drive(self):
        with tempfile.TemporaryDirectory() as tmp:
            sha = self.repo(tmp)
            code, data, rows = audit(tmp)
            self.assertEqual(code, 0, data)
            self.assertEqual(data["since"], sha)
            self.assertEqual(rows["Thing"]["action"], "drive")
            self.assertTrue(rows["Thing"]["proven"])
            self.assertEqual(data["verdict"], "green")

    def test_product_churn_since_last_pass_is_re_drive_and_new_files_unclaimed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.repo(tmp)
            write(tmp, "src/app.py", "VALUE = 43\n")
            write(tmp, "tools/export.py", "print(1)\n")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-qm", "feature work")
            code, data, rows = audit(tmp)
            self.assertEqual(code, 1)
            self.assertEqual((rows["Thing"]["action"], rows["Thing"]["changed"]), ("re-drive", ["src/app.py"]))
            self.assertEqual(data["unclaimed_changes"], ["tools/export.py"])
            self.assertEqual(audit(tmp, "--since", "HEAD")[2]["Thing"]["action"], "drive")
            out = run("verify.py", "maintain", tmp)[1]
            self.assertIn("RE-DRIVE  Thing", out)
            self.assertIn("UNCLAIMED tools/export.py", out)

    def test_red_last_run_is_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.repo(tmp)
            os.remove(os.path.join(tmp, "ok.flag"))
            run("verify.py", "run", tmp)
            self.assertEqual(audit(tmp)[2]["Thing"]["action"], "fix")

    def test_feature_without_a_map_file_is_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.repo(tmp)
            os.remove(os.path.join(tmp, ".claude", "skills", "verify", "features", "thing.md"))
            code, data, rows = audit(tmp)
            self.assertEqual(rows["Thing"]["action"], "map")
            self.assertTrue(any("no feature files" in p for p in data["shape"]))

    def test_changed_check_needs_review_and_fresh_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.repo(tmp)
            write(tmp, "check.py", "import sys\nsys.exit(0)\n")
            code, data, rows = audit(tmp)
            self.assertEqual(code, 1)
            self.assertIn("check.py", data["baseline_drift"])
            self.assertEqual(rows["Thing"]["action"], "re-prove")
            self.assertFalse(rows["Thing"]["proven"])
            self.assertIn("BASELINE  check.py differs", run("verify.py", "maintain", tmp)[1])

    def test_a_reviewed_and_rebaselined_check_change_is_not_churn(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.repo(tmp)
            with open(os.path.join(tmp, "check.py"), "a", encoding="utf-8") as fh:
                fh.write("# reviewed wording\n")
            git(tmp, "commit", "-qam", "harness repair")
            run("verify.py", "baseline", tmp)
            os.remove(os.path.join(tmp, "ok.flag"))
            run("verify.py", "run", tmp)
            write(tmp, "ok.flag")
            run("verify.py", "run", tmp, "--strict")
            code, data, rows = audit(tmp)
            self.assertEqual((code, rows["Thing"]["action"]), (0, "drive"), data)

    def test_without_git_churn_is_skipped_not_invented(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, ".claude/skills/verify/SKILL.md", SKILL)
            write(tmp, "VERIFY.md", f"## Thing\n- test: `{CHECK}`\n")
            code, data, _ = audit(tmp)
            self.assertFalse(data["git"])
            self.assertEqual(data["unclaimed_changes"], [])
            self.assertIn("churn not checked", run("verify.py", "maintain", tmp)[1])


if __name__ == "__main__":
    unittest.main()
