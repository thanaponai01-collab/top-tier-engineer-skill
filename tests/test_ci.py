"""Fresh committed inputs, actual negative runs, and failure artifacts through the CLI."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _helpers import run


class CI(unittest.TestCase):
    def fixture(self, tmp, hollow=False):
        root = Path(tmp, "project")
        root.mkdir()
        (root / "app.py").write_text("def answer(): return 42\n")
        assertion = "self.assertTrue(True)" if hollow else "self.assertEqual(answer(), 42, 'expected 42')"
        (root / "test_answer.py").write_text("import unittest\nfrom app import answer\n"
                                            "class TestAnswer(unittest.TestCase):\n"
                                            f"    def test_answer(self): {assertion}\n")
        (root / "VERIFY.md").write_text("## Answer\n- test: `python -m unittest test_answer.py`\n"
                                       "- fail-signal: expected 42\n- fail-proof: return 41 instead of 42 in scratch\n")
        (root / "mutation.json").write_text(json.dumps({"file": "app.py", "before": "return 42",
                                                       "after": "return 41", "claim": "answer is 42"}))
        (root / "ci.json").write_text(json.dumps([{"feature": "Answer", "mutation": "mutation.json"}]))
        (root / ".gitignore").write_text(".verify-state.json\n__pycache__/\n")
        self.git(root, "init", "-q")
        self.git(root, "add", ".")
        self.commit(root)
        return root

    def git(self, root, *args):
        p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)
        return p.stdout.strip()

    def commit(self, root):
        self.git(root, "-c", "user.name=CI Test", "-c", "user.email=ci@example.invalid", "commit", "-qm", "fixture")

    def ci(self, root, out):
        return run("verify.py", "ci", str(root), "--plan", "ci.json", "--output", str(out))

    def test_fresh_proof_ignores_local_state_and_records_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            local = root / ".verify-state.json"
            local.write_text('{"result": "green", "strict": true, "local_only": true}')
            self.git(root, "add", "-f", ".verify-state.json")
            self.commit(root)
            before = local.read_bytes()
            out = Path(tmp, "evidence")
            code, stdout, stderr = self.ci(root, out)
            self.assertEqual(code, 0, stdout + stderr)
            report = json.loads((out / "report.json").read_text())
            self.assertEqual(report["verdict"], "green")
            self.assertEqual(report["commit"], self.git(root, "rev-parse", "HEAD"))
            state = json.loads((out / "state.json").read_text())
            self.assertTrue(state["strict"])
            self.assertNotIn("local_only", state)
            self.assertEqual(local.read_bytes(), before)
            self.assertEqual(self.git(root, "status", "--porcelain"), "")

    def test_survivor_fails_with_evidence_even_if_local_state_claims_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp, hollow=True)
            (root / ".verify-state.json").write_text('{"result": "green", "strict": true}')
            out = Path(tmp, "evidence")
            code, stdout, stderr = self.ci(root, out)
            self.assertEqual(code, 1, stdout + stderr)
            report = json.loads((out / "report.json").read_text())
            self.assertEqual(report["verdict"], "red")
            self.assertIn("survived", (out / "run.log").read_text())

    def test_wrong_committed_product_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root / "app.py").write_text("def answer(): return 41\n")
            self.git(root, "add", "app.py")
            self.commit(root)
            code, stdout, stderr = self.ci(root, Path(tmp, "evidence"))
            self.assertEqual(code, 1, stdout + stderr)

    def test_dirty_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root / "app.py").write_text("def answer(): return 41\n")
            code, stdout, stderr = self.ci(root, Path(tmp, "evidence"))
            self.assertEqual(code, 1, stdout + stderr)
            self.assertIn("clean", stdout)

    def test_empty_plan_cannot_pass_using_imported_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root / "ci.json").write_text("[]")
            self.git(root, "add", "ci.json")
            self.commit(root)
            self.assertEqual(self.ci(root, Path(tmp, "evidence"))[0], 1)

    def test_output_inside_checkout_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            code, stdout, stderr = self.ci(root, root / "evidence")
            self.assertNotEqual(code, 0, stdout + stderr)
            self.assertFalse((root / "evidence").exists())

    def test_committed_project_subdirectory_is_exported_from_git_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            nested = root / "application"
            nested.mkdir()
            for path in list(root.iterdir()):
                if path.is_file():
                    self.git(root, "mv", path.name, "application/" + path.name)
            self.commit(root)
            out = Path(tmp, "evidence")
            code, stdout, stderr = self.ci(nested, out)
            self.assertEqual(code, 0, stdout + stderr)
            report = json.loads((out / "report.json").read_text())
            self.assertEqual(report["project_path"], "application")
