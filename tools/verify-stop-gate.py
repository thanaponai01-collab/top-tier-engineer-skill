#!/usr/bin/env python3
"""
verify-stop-gate — stops "done" from being said over a red, stale or tampered verify run.

The loop in verify-loop is only closed if something notices when the agent stops without
running it. This hook asks `verify.py status` at Stop and, when the answer is not green,
blocks the stop ONCE so the agent runs the check and reports the result.

WHY A STOP HOOK AGAIN
---------------------
An earlier Stop hook was deleted in c479319: it linted this suite's own verdict lines and
could wedge a session over a malformed one. This one differs on the three counts that mattered:

  1. It judges the user's work (`verify.py status`), not the suite's own output.
  2. It is opt-in per repo: no VERIFY.md, or no source edit in this session, means silence.
  3. It blocks at most once per (session, state). A second stop with the same state always
     passes, so it can nudge but never trap. A gate that traps gets uninstalled.

Blocking is exit 2 with the reason on stderr, which is what the hooks docs give for Stop.
The legacy reminder fails open (exit 0, no output). Driven runs below fail closed on invalid
evidence, with an explicit blocked/failed handoff escape so stopping never requires faking success.
Set TTE_VERIFY_STOP=0 to turn it off. Repos with RUN.json opt into drive's strict
completion gate; blocked/failed handoffs remain allowed. No RUN.json retains
the one-time reminder described above. This is not an independent security boundary.

Usage:  Stop hook via hooks/hooks.json (payload on stdin)
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERIFY = HERE.parent / "skills" / "verify-loop" / "scripts" / "verify.py"
RUN = HERE.parent / "skills" / "drive" / "scripts" / "run.py"

_spec = importlib.util.spec_from_file_location("unproven_gate", HERE / "unproven-gate.py")
_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gate)


def find_repo(start):
    """The nearest directory at or above `start` holding a VERIFY.md, or None."""
    p = Path(start).resolve()
    for d in [p, *list(p.parents)[:6]]:
        if (d / "VERIFY.md").is_file():
            return d
    return None


def session_edited(lines):
    """True if this session wrote any file. A chat that changed nothing has nothing to verify."""
    return any(tool in _gate.EDIT_TOOLS for tool, _ in _gate._tool_calls(lines))


def status(repo):
    """(exit code, the one status line) from `verify.py status`, or (0, '') if it cannot answer."""
    try:
        p = subprocess.run([sys.executable, str(VERIFY), "status", str(repo)], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=8)
    except (OSError, subprocess.SubprocessError):
        return 0, ""
    return p.returncode, (p.stdout or "").strip().splitlines()[-1] if (p.stdout or "").strip() else ""


def already_blocked(session_id, line):
    """True if this exact state was already blocked in this session. Marks it if not."""
    key = hashlib.sha256((str(session_id) + "\0" + line).encode("utf-8")).hexdigest()[:32]
    marker = Path(tempfile.gettempdir()) / "tte-verify-stop-gate" / key
    try:
        if marker.exists():
            return True
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("", encoding="utf-8")
    except OSError:
        return True  # cannot record the block, so cannot promise it happens once: do not block
    return False


def reason(line):
    return (f"[top-tier-engineer] {line}\n"
            f"Before you stop: run `python \"{VERIFY}\" run` in the repo and report the result, "
            "or say plainly why you cannot. Fix the code, never the check: an edited check fails the run. "
            "This blocks once.")


def drive_stop(start):
    """None when no durable run; otherwise a strict gate with an honest-stop escape."""
    for repo in [Path(start).resolve(), *list(Path(start).resolve().parents)[:6]]:
        path = repo / "RUN.json"
        if not path.is_file():
            continue
        try:
            state = json.loads(path.read_text(encoding="utf-8-sig"))
            if (state.get("status") in {"blocked", "failed"}
                    and isinstance(state.get("reason"), str) and state["reason"].strip()
                    and isinstance(state.get("next_action"), str) and state["next_action"].strip()):
                return 0, ""  # Handoff, not completion. Preserve uncertain actions.
            proc = subprocess.run([sys.executable, str(RUN), "--repo", str(repo), "status"],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  timeout=8)
            if proc.returncode == 0:
                return 0, ""
            detail = (proc.stdout + proc.stderr).strip()[-1500:]
        except (OSError, ValueError, AttributeError, subprocess.SubprocessError) as exc:
            detail = str(exc)
        return 2, ("[top-tier-engineer] " + detail + "\n"
                   "RUN.json cannot claim completion. Continue with drive's run.py next/check/finish, "
                   "or record an honest stop with run.py stop blocked|failed --reason ... --next ... . "
                   "This gate remains closed until evidence passes or a handoff is recorded.")
    return None


def main():
    if os.environ.get("TTE_VERIFY_STOP") == "0":
        return 0
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    # Driven runs are opt-in and strict, including resumed sessions without edits.
    driven = drive_stop(payload.get("cwd") or os.getcwd())
    if driven is not None:
        code, detail = driven
        if detail:
            print(detail, file=sys.stderr)
        return code
    transcript = payload.get("transcript_path")
    if not transcript or not os.path.isfile(transcript):
        return 0
    if not session_edited(_gate._tail_lines(transcript)):
        return 0
    repo = find_repo(payload.get("cwd") or os.getcwd())
    if not repo:
        return 0
    code, line = status(repo)
    if code == 0 or not line:
        return 0
    if already_blocked(payload.get("session_id"), line):
        return 0
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        pass
    print(reason(line), file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0  # a bug here must never hold a session open
    sys.exit(code)
