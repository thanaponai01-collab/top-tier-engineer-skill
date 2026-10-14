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
SCRIPTS = ROOT / "plugin" / "scripts"
GATE = SCRIPTS / "unproven-gate.py"
STOP_GATE = SCRIPTS / "verify-stop-gate.py"
VERIFY = ROOT / "plugin" / "skills" / "verify-loop" / "scripts" / "verify.py"

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


def run_hook(script, payload, cwd=None):
    """Invoke a hook through its CLI the way Claude Code does."""
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload), capture_output=True, text=True,
        encoding="utf-8", cwd=cwd,
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


class TestHooksManifest(unittest.TestCase):
    def test_explicit_entry_profiles(self):
        for name in ('hooks.json', 'optional.json', 'autonomous.json'):
            manifest = json.loads((ROOT / 'plugin' / 'hooks' / name).read_text())
            self.assertEqual(set(manifest['hooks']), set() if name == 'hooks.json' else {'Stop'})
        for path in (ROOT / 'plugin' / 'skills').glob('*/SKILL.md'):
            self.assertIn('disable-model-invocation: true', path.read_text(encoding='utf-8').split('---', 2)[1])

    def test_opt_in_profiles_point_at_shipped_scripts(self):
        for name in ('optional.json', 'autonomous.json'):
            text = (ROOT / 'plugin' / 'hooks' / name).read_text(encoding='utf-8-sig')
            self.assertIn('${CLAUDE_PLUGIN_ROOT}/scripts/verify-stop-gate.py', text)
        self.assertTrue((SCRIPTS / 'verify-stop-gate.py').is_file())


class TestVerifyStopGate(unittest.TestCase):
    """Blocks a stop over a not-green verify run at most once, and otherwise says nothing."""

    def _repo(self, tmp, green):
        (Path(tmp) / "VERIFY.md").write_text(
            "## Thing\n- test: `python -c \"from pathlib import Path; "
            "assert Path('ok.flag').exists(), 'missing flag'\"`\n"
            "- fail-signal: missing flag\n- fail-proof: removed flag, assertion failed\n",
            encoding="utf-8")
        subprocess.run([sys.executable, str(VERIFY), "run", tmp], capture_output=True)
        if green:
            subprocess.run([sys.executable, str(VERIFY), "baseline", tmp], capture_output=True)
            (Path(tmp) / "ok.flag").write_text("ok", encoding="utf-8")
            subprocess.run([sys.executable, str(VERIFY), "run", tmp, "--strict"], capture_output=True)

    def _payload(self, tmp, lines, sid):
        path = Path(tmp) / "transcript.jsonl"
        path.write_text("\n".join(lines), encoding="utf-8")
        return {"transcript_path": str(path), "cwd": tmp, "session_id": sid}

    def test_red_run_after_an_edit_blocks_once_with_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, green=False)
            payload = self._payload(tmp, [edit("src/api.py")], "stop-red-%s" % os.getpid())
            code, _, err = run_hook(STOP_GATE, payload)
            self.assertEqual(code, 2)
            self.assertIn("VERIFY-STATE: red", err)
            self.assertIn("verify.py", err)
            code, _, err = run_hook(STOP_GATE, payload)
            self.assertEqual((code, err.strip()), (0, ""), "the second stop must pass: nudge, never trap")

    def test_stale_green_blocks_and_a_fresh_green_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, green=True)
            payload = self._payload(tmp, [edit("src/api.py")], "stop-green-%s" % os.getpid())
            (Path(tmp) / "later.py").write_text("x = 1\n", encoding="utf-8")
            code, _, err = run_hook(STOP_GATE, dict(payload, session_id="stop-stale-%s" % os.getpid()))
            self.assertEqual(code, 2)
            self.assertIn("stale", err)
            subprocess.run([sys.executable, str(VERIFY), "run", tmp, "--strict"], capture_output=True)
            code, _, err = run_hook(STOP_GATE, dict(payload, session_id="stop-fresh-%s" % os.getpid()))
            self.assertEqual((code, err.strip()), (0, ""))

    def test_silent_when_nothing_was_edited_or_no_verify_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, green=False)
            code, _, err = run_hook(STOP_GATE, self._payload(tmp, [bash("pytest -q")], "stop-noedit-%s" % os.getpid()))
            self.assertEqual((code, err.strip()), (0, ""), "a session that wrote nothing has nothing to verify")
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_hook(STOP_GATE, self._payload(tmp, [edit("src/api.py")], "stop-norepo-%s" % os.getpid()))
            self.assertEqual((code, err.strip()), (0, ""), "no VERIFY.md: not this repo's business")

    def test_env_switch_turns_it_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._repo(tmp, green=False)
            payload = self._payload(tmp, [edit("src/api.py")], "stop-off-%s" % os.getpid())
            proc = subprocess.run([sys.executable, str(STOP_GATE)], input=json.dumps(payload),
                                  capture_output=True, text=True, env=dict(os.environ, TTE_VERIFY_STOP="0"))
            self.assertEqual(proc.returncode, 0)

    def test_every_malformed_payload_exits_zero_and_silent(self):
        # A payload without cwd falls back to the process's own directory; run from an empty one, so
        # an active RUN.json in whatever checkout runs the suite is not what this test measures.
        with tempfile.TemporaryDirectory() as empty:
            for payload in ({}, {"transcript_path": "/nonexistent/x.jsonl"}, {"transcript_path": None},
                            {"session_id": "x", "cwd": "/nonexistent"}):
                code, _, err = run_hook(STOP_GATE, payload, cwd=empty)
                self.assertEqual((code, err.strip()), (0, ""), payload)
        proc = subprocess.run([sys.executable, str(STOP_GATE)], input="not json", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)


class TestDriveStopGate(unittest.TestCase):
    def test_active_run_blocks_repeatedly_without_source_edits(self):
        from test_drive_run import RunGate
        sample = RunGate()
        sample.setUp()
        try:
            sample.init()
            payload = {"cwd": str(sample.root), "session_id": "drive-resume"}
            for _ in range(2):
                code, _, err = run_hook(STOP_GATE, payload)
                self.assertEqual(code, 2)
                self.assertIn("RUN.json cannot claim completion", err)
            sample.call("check", "prove")
            sample.call("finish")
            self.assertEqual(run_hook(STOP_GATE, payload)[0], 0)
            sample.put("app.py", "VALUE = 9\n")
            self.assertEqual(run_hook(STOP_GATE, payload)[0], 2)
            sample.call("stop", "failed", "--reason", "evidence stale", "--next", "recheck source")
            self.assertEqual(run_hook(STOP_GATE, payload)[0], 0)
        finally:
            sample.doCleanups()

    def test_invalid_record_blocks_but_an_honest_handoff_can_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "RUN.json"
            payload = {"cwd": tmp}
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(run_hook(STOP_GATE, payload)[0], 2)
            path.write_text(json.dumps({"status": "blocked"}), encoding="utf-8")
            self.assertEqual(run_hook(STOP_GATE, payload)[0], 2)
            path.write_text(json.dumps({"status": "blocked", "reason": "record damaged",
                                       "next_action": "restore the journal from backup"}), encoding="utf-8")
            self.assertEqual(run_hook(STOP_GATE, payload)[0], 0)


if __name__ == "__main__":
    unittest.main()
