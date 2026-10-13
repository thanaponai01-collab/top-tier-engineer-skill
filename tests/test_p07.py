"""P07 exercises a live stale process against source and runtime identity."""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from urllib.request import urlopen

from _helpers import ROOT, run

FIXTURE = Path(ROOT) / "evals/fixtures/p07"


class RunningArtifactIdentity(unittest.TestCase):
    def test_behavior_prompt_does_not_leak_the_expected_revision_token(self):
        case = Path(ROOT) / "evals/cases/p07-running-artifact-identity"
        for name in ("prompt.md", "prompt-plain.md"):
            with self.subTest(prompt=name):
                prompt = (case / name).read_text(encoding="utf-8").lower()
                self.assertNotIn("head", prompt)

    def test_verify_loop_guides_material_running_artifact_identity(self):
        skill = (Path(ROOT) / "skills/verify-loop/SKILL.md").read_text(encoding="utf-8").lower()
        format_doc = (Path(ROOT) / "skills/verify-loop/VERIFY_FORMAT.md").read_text(encoding="utf-8").lower()
        combined = skill + "\n" + format_doc
        for term in ("source", "dirty", "flags", "role", "mock", "head"):
            with self.subTest(term=term):
                self.assertIn(term, combined)
        self.assertIn("running artifact identity", combined)
        self.assertIn("head alone", combined)

    def fixture(self, root, port, managed=True):
        shutil.copytree(FIXTURE, root, dirs_exist_ok=True)
        config = {
            "port": port,
            "flags": ["--mode=production", "--workers=2"],
            "role": "api", "mocks": ["mail-sink"],
        }
        (root / "config.json").write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
        recipe = "## Identity\n- test: `python -c \"open('check-ran','w').write('yes')\"`\n"
        recipe += "- fail-proof: changed the running source while the prior server stayed responsive\n\n## Run\n"
        if managed:
            recipe += "- start: `python app.py serve`\n- ready: `python ready.py`\n"
        recipe += "- doctor: `python doctor.py`\n"
        (root / "VERIFY.md").write_text(recipe, encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "p07@example.test"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "P07 Test"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "app.py", "doctor.py", "config.json", "VERIFY.md"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        return config

    def launch(self, root):
        proc = subprocess.Popen([sys.executable, "app.py", "serve"], cwd=root,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{json.loads((root / 'config.json').read_text())['port']}/identity", timeout=.2):
                    return proc
            except Exception:
                if proc.poll() is not None:
                    self.fail("control server exited before readiness")
                time.sleep(.03)
        proc.terminate()
        proc.wait(timeout=3)
        self.fail("control server did not become ready")

    def exercise_stale(self, changed):
        with tempfile.TemporaryDirectory() as current_tmp, tempfile.TemporaryDirectory() as old_tmp:
            current, old = Path(current_tmp), Path(old_tmp)
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            config = self.fixture(current, port, managed=False)
            subprocess.run(["git", "clone", "-q", str(current), str(old)], check=True)
            current_head = subprocess.check_output(["git", "-C", str(current), "rev-parse", "HEAD"], text=True).strip()
            old_head = subprocess.check_output(["git", "-C", str(old), "rev-parse", "HEAD"], text=True).strip()
            self.assertEqual(current_head, old_head)
            proc = self.launch(old)
            try:
                if changed == "source_sha256":
                    with (current / "app.py").open("a", encoding="utf-8") as stream:
                        stream.write("\n# uncommitted source change\n")
                else:
                    config[changed] = ["--mode=staging"] if changed == "flags" else ("worker" if changed == "role" else ["mail-live"])
                    (current / "config.json").write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
                self.assertEqual(current_head, subprocess.check_output(["git", "-C", str(current), "rev-parse", "HEAD"], text=True).strip())
                result = run("verify.py", "run", str(current), "--timeout", "6")
                output = result[1] + result[2]
                self.assertEqual(result[0], 1, output)
                self.assertIn(changed, output)
                state = json.loads((current / ".verify-state.json").read_text(encoding="utf-8"))
                self.assertIn(changed, state["doctor"]["output"])
                self.assertFalse((current / "check-ran").exists(), "checks ran against stale process")
                self.assertIsNone(proc.poll(), "healthy old process was terminated")
                with urlopen(f"http://127.0.0.1:{port}/identity", timeout=1) as response:
                    self.assertEqual(json.load(response)["pid"], proc.pid)
            finally:
                proc.terminate()
                proc.wait(timeout=3)

    def test_healthy_old_process_is_rejected_for_uncommitted_source_on_same_head(self):
        self.exercise_stale("source_sha256")

    def test_healthy_old_process_is_rejected_for_flags_roles_and_mock_boundaries(self):
        for field in ("flags", "role", "mocks"):
            with self.subTest(field=field):
                self.exercise_stale(field)

    def test_current_process_identity_is_retained_by_the_run_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.fixture(root, 0, managed=True)
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                config["port"] = sock.getsockname()[1]
            (root / "config.json").write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
            code, out, err = run("verify.py", "run", str(root), "--timeout", "6")
            self.assertEqual(code, 0, out + err)
            state = json.loads((root / ".verify-state.json").read_text(encoding="utf-8"))
            for field in ("source_sha256", "config_sha256", "flags", "role", "mocks", "pid"):
                self.assertIn(field, state["doctor"]["output"])

