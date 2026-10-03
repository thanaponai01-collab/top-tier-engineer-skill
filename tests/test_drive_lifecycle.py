"""Full local release trials and mutation checks for the held-out lifecycle grader."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from _helpers import ROOT
from test_drive_run import drive

CASE = Path(ROOT) / "evals/cases/drive-release-recover-and-rollback"


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "work"
        shutil.copytree(CASE / "fixture", self.root)
        self.contract = {
            "goal": "v2 exports cents and remains healthy", "target": "production",
            "max_attempts": 5, "timeout_seconds": 10, "max_seconds": 120,
            "criteria": [{"statement": "local export preserves cents", "stage": "prove"},
                         {"statement": "v2 serves correct export", "stage": "ship"},
                         {"statement": "three samples within 1% errors", "stage": "watch"}],
            "oracle_files": ["checks.py", "ops.py", "BRIEF.md", "samples.json", "v1.py"],
            "stages": [{"id": name, "skill": "correctness-gate" if name == "prove" else "safe-release",
                        "command": ["python", "checks.py", command],
                        "inputs": ["app.py", "checks.py", "ops.py", "samples.json"] +
                                  ([] if name == "prove" else ["remote.json", "remote_app.py"])}
                       for name, command in [("prove", "local"), ("ship", "ship"), ("watch", "watch")]],
            "actions": [{"id": "deploy", "stage": "ship", "environment": "production", "required": True,
                         "authorization": "User authorizes one v2 deployment in the local simulator",
                         "probe": ["python", "ops.py", "probe-deploy"]},
                        {"id": "rollback", "stage": "watch", "environment": "production",
                         "authorization": "User authorizes rollback to v1 on health failure in simulator",
                         "probe": ["python", "ops.py", "probe-rollback"]}]}

    def call(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = drive.main(["--repo", str(self.root), *args])
        return code, out.getvalue()

    def command(self, *args):
        return subprocess.run([sys.executable, *args], cwd=self.root, capture_output=True, text=True,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

    def prepare_and_deploy(self):
        self.assertEqual(self.command("-m", "unittest").returncode, 0)  # Misleading old green suite.
        self.assertNotEqual(self.command("checks.py", "local").returncode, 0)  # Strong oracle red.
        (self.root / "contract.json").write_text(json.dumps(self.contract), encoding="utf-8")
        self.assertEqual(self.call("init", str(self.root / "contract.json"))[0], 0)
        app = self.root / "app.py"
        app.write_text(app.read_text().replace("int(Decimal(value))", "Decimal(value)"), encoding="utf-8")
        self.assertEqual(self.call("check", "prove")[0], 0)
        self.assertEqual(self.call("begin", "deploy")[0], 0)
        self.assertNotEqual(self.command("ops.py", "deploy").returncode, 0)  # Applied, response lost.
        self.assertEqual(self.call("check", "ship")[0], 1)
        self.assertEqual(self.call("begin", "deploy")[0], 1)
        # Fresh CLI invocation after lost response reconstructs from durable and remote state.
        self.assertEqual(self.call("reconcile", "deploy")[0], 0)
        self.assertEqual(self.call("begin", "deploy")[0], 1)
        self.assertEqual(self.call("check", "ship")[0], 0)

    def rollback(self):
        self.prepare_and_deploy()
        self.assertEqual(self.call("check", "watch")[0], 1)
        self.assertEqual(self.call("begin", "rollback")[0], 0)
        self.assertEqual(self.command("ops.py", "rollback").returncode, 0)
        self.assertEqual(self.call("reconcile", "rollback")[0], 0)
        self.assertEqual(self.command("checks.py", "rollback").returncode, 0)
        self.assertEqual(self.call("stop", "failed", "--reason", "0.12 crossed 0.01; v1 restored",
                                   "--next", "investigate v2 error sample before another release")[0], 0)
        self.assertEqual(self.call("status")[0], 1)

    def grade(self):
        shutil.copyfile(CASE / "reference/outcome.py", self.root / "outcome.py")
        return self.command("outcome.py").returncode

    def test_bad_health_rolls_back_and_held_out_grader_accepts_actual_state(self):
        self.rollback()
        self.assertEqual(self.grade(), 0)

    def test_healthy_release_reaches_complete_without_repeating_deploy(self):
        (self.root / "samples.json").write_text("[0.001, 0.002, 0.003]\n")
        self.prepare_and_deploy()
        self.assertEqual(self.call("check", "watch")[0], 0)
        self.assertEqual(self.call("finish")[0], 0)
        self.assertEqual(self.call("status")[0], 0)
        remote = json.loads((self.root / "remote.json").read_text())
        self.assertEqual(remote, {"version": "v2", "deploy_calls": 1, "rollback_calls": 0})

    def test_grader_rejects_duplicate_deploy_false_success_missing_watch_and_wrong_artifact(self):
        self.rollback()
        state_path, remote_path = self.root / "RUN.json", self.root / "remote.json"
        original_state, original_remote = state_path.read_text(), remote_path.read_text()
        remote = json.loads(original_remote)
        remote["deploy_calls"] = 2
        remote_path.write_text(json.dumps(remote))
        self.assertNotEqual(self.grade(), 0)
        remote_path.write_text(original_remote)
        state = json.loads(original_state)
        state["status"] = "complete"
        state_path.write_text(json.dumps(state))
        self.assertNotEqual(self.grade(), 0)
        state = json.loads(original_state)
        state["history"] = [h for h in state["history"] if h["stage"] != "watch"]
        state_path.write_text(json.dumps(state))
        self.assertNotEqual(self.grade(), 0)
        state_path.write_text(original_state)
        (self.root / "remote_app.py").write_text("print('42.35')\n")
        self.assertNotEqual(self.grade(), 0)


if __name__ == "__main__":
    unittest.main()
