"""Tests for the two shipped hooks.

A hook that misfires is worse than no hook: this plugin already deleted one Stop
hook that could wedge a session (c479319). So these tests weigh two things —
that the gate finds unproven edits, and that it stays silent and exits 0 on
every malformed input it could ever be handed.

Run everything with: python -m unittest discover tests
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
GATE = TOOLS / "unproven-gate.py"
PHILOSOPHY_HOOK = TOOLS / "philosophy-hook.py"

# The hooks are hyphenated CLI scripts, so they are loaded by path rather than
# imported by name.
_spec = importlib.util.spec_from_file_location("unproven_gate", GATE)
unproven_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(unproven_gate)


def tool_use(name, payload):
    """One transcript line carrying a single tool_use block."""
    return json.dumps({
        "type": "assistant",
        "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": name, "input": payload}
        ]},
    })


def edit(path):
    return tool_use("Edit", {"file_path": path})


def bash(command):
    return tool_use("Bash", {"command": command})


def run_hook(script, payload):
    """Invoke a hook through its CLI the way Claude Code does."""
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload), capture_output=True, text=True,
        encoding="utf-8",
    )
    return proc.returncode, proc.stdout, proc.stderr


class TestRunDetection(unittest.TestCase):
    def test_test_runners_count_as_running(self):
        for command in ("pytest -q", "npm test", "go test ./...",
                        "python -m unittest discover tests", "./app --check"):
            self.assertTrue(unproven_gate.runs_something(command), command)

    def test_reading_is_not_proving(self):
        # Under bypass mode an agent reads with Bash constantly. If these
        # counted, the gate would read a session where nothing ran as proven.
        for command in ("cat src/api.py", "grep -rn foo .", "ls -la",
                        "git status", "git diff HEAD~1", "sed -n '1,40p' x.py"):
            self.assertFalse(unproven_gate.runs_something(command), command)

    def test_a_real_command_anywhere_in_the_line_counts(self):
        self.assertTrue(unproven_gate.runs_something("cat x.py && pytest"))
        self.assertTrue(unproven_gate.runs_something("git status; npm run build"))
        self.assertFalse(unproven_gate.runs_something("git status && grep x y"))

    def test_env_prefixes_and_sudo_are_stepped_over(self):
        self.assertTrue(unproven_gate.runs_something("DEBUG=1 pytest"))
        self.assertFalse(unproven_gate.runs_something("DEBUG=1 cat x"))

    def test_mutating_git_counts(self):
        self.assertTrue(unproven_gate.runs_something("git push"))
        self.assertTrue(unproven_gate.runs_something("git commit -m x"))


class TestSourceDetection(unittest.TestCase):
    def test_code_is_source(self):
        for path in ("a/b.py", "src/x.ts", "main.go", "lib/y.rs"):
            self.assertTrue(unproven_gate.is_source(path), path)

    def test_prose_and_config_are_not(self):
        for path in ("README.md", "CHANGELOG.md", "package.json", "x.yml", ""):
            self.assertFalse(unproven_gate.is_source(path), path)


class TestUnprovenFiles(unittest.TestCase):
    def test_edit_with_no_run_is_flagged(self):
        lines = [edit("src/api.py")]
        self.assertEqual(unproven_gate.unproven_files(lines), ["src/api.py"])

    def test_edit_then_run_is_clean(self):
        lines = [edit("src/api.py"), bash("pytest -q")]
        self.assertEqual(unproven_gate.unproven_files(lines), [])

    def test_run_then_edit_is_flagged(self):
        # The order that actually matters: proving, then changing, proves nothing.
        lines = [bash("pytest -q"), edit("src/api.py")]
        self.assertEqual(unproven_gate.unproven_files(lines), ["src/api.py"])

    def test_edit_followed_only_by_reads_is_flagged(self):
        lines = [edit("src/api.py"), bash("cat src/api.py"), bash("git diff")]
        self.assertEqual(unproven_gate.unproven_files(lines), ["src/api.py"])

    def test_markdown_only_session_is_clean(self):
        lines = [edit("README.md"), edit("docs/plan.md")]
        self.assertEqual(unproven_gate.unproven_files(lines), [])

    def test_malformed_lines_are_skipped_not_fatal(self):
        lines = ["", "garbage", "{bad json", json.dumps({"no": "message"}),
                 json.dumps({"message": "not a dict"}), edit("src/api.py")]
        self.assertEqual(unproven_gate.unproven_files(lines), ["src/api.py"])

    def test_multiple_files_are_sorted(self):
        lines = [edit("src/z.py"), edit("src/a.py")]
        self.assertEqual(unproven_gate.unproven_files(lines),
                         ["src/a.py", "src/z.py"])


class TestMessage(unittest.TestCase):
    def test_silent_when_nothing_unproven(self):
        self.assertEqual(unproven_gate.message([]), "")

    def test_names_the_files_and_the_labels(self):
        text = unproven_gate.message(["src/api.py", "src/db.py"])
        self.assertIn("api.py", text)
        self.assertIn("db.py", text)
        for label in ("proven", "traced", "suspected"):
            self.assertIn(label, text)

    def test_long_lists_are_truncated(self):
        text = unproven_gate.message(["src/f%d.py" % i for i in range(9)])
        self.assertIn("+5 more", text)


class TestFailsOpen(unittest.TestCase):
    """Exit 2 on UserPromptSubmit erases the user's prompt. Never happens."""

    def test_every_malformed_payload_exits_zero_and_silent(self):
        for payload in ({}, {"transcript_path": "/nonexistent/x.jsonl"},
                        {"transcript_path": None}, {"session_id": "x"}):
            code, out, _ = run_hook(GATE, payload)
            self.assertEqual(code, 0, payload)
            self.assertEqual(out.strip(), "", payload)

    def test_non_json_stdin_exits_zero(self):
        proc = subprocess.run([sys.executable, str(GATE)], input="not json",
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)

    def test_end_to_end_flags_a_real_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transcript.jsonl"
            path.write_text("\n".join([bash("pytest -q"), edit("src/api.py")]),
                            encoding="utf-8")
            code, out, _ = run_hook(GATE, {
                "transcript_path": str(path),
                "session_id": "test-%s" % os.getpid(),
            })
            self.assertEqual(code, 0)
            self.assertIn("api.py", out)

    def test_same_finding_is_not_repeated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transcript.jsonl"
            path.write_text(edit("src/api.py"), encoding="utf-8")
            payload = {"transcript_path": str(path),
                       "session_id": "dedupe-%s" % os.getpid()}
            first = run_hook(GATE, payload)[1]
            second = run_hook(GATE, payload)[1]
            self.assertIn("api.py", first)
            self.assertEqual(second.strip(), "")


class TestPhilosophyHook(unittest.TestCase):
    def test_emits_the_philosophy(self):
        code, out, _ = run_hook(PHILOSOPHY_HOOK, {"hook_event_name": "SessionStart"})
        self.assertEqual(code, 0)
        self.assertIn("Understand before you change", out)
        self.assertIn("Ground truth over memory", out)

    def test_exits_zero_on_garbage(self):
        # Exit 2 on SessionStart prevents the session from starting at all.
        proc = subprocess.run([sys.executable, str(PHILOSOPHY_HOOK)],
                              input="garbage", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)


class TestHooksManifest(unittest.TestCase):
    def test_manifest_is_valid_and_points_at_real_scripts(self):
        manifest = json.loads((ROOT / "hooks" / "hooks.json")
                              .read_text(encoding="utf-8-sig"))
        events = manifest["hooks"]
        self.assertIn("SessionStart", events)
        self.assertIn("UserPromptSubmit", events)
        referenced = json.dumps(manifest)
        for script in ("philosophy-hook.py", "unproven-gate.py"):
            self.assertIn(script, referenced)
            self.assertTrue((TOOLS / script).is_file(), script)

    def test_no_stop_hook(self):
        # The Stop hook was deleted in c479319 for blocking sessions. Reaching
        # the model from Stop still requires decision:"block". If a Stop entry
        # ever reappears here, it is a deliberate decision that needs its own
        # justification — not something that drifted back in.
        manifest = json.loads((ROOT / "hooks" / "hooks.json")
                              .read_text(encoding="utf-8-sig"))
        self.assertNotIn("Stop", manifest["hooks"])


if __name__ == "__main__":
    unittest.main()
