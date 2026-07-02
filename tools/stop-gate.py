#!/usr/bin/env python3
"""
stop-gate — Stop-hook adapter for verdict-lint (the mechanical enforcement floor).

Reads the hook payload on stdin, extracts assistant text from the transcript JSONL,
and lints it against PROTOCOL §5 form rules. When the session's cwd is the plugin
repo itself, also runs the release check (plugin.json version vs CHANGELOG top entry).
Violations block the stop (exit 2, findings on stderr) so a session cannot declare
done past a broken ledger. Sessions with no verdict lines pass untouched — the gate
is silent outside suite runs.

Fails open: any internal error exits 0. A lint tool must never wedge a session
on its own bug.

Usage:  Stop hook via hooks/hooks.json (payload on stdin)
        stop-gate.py --selftest
"""
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def _load_lint():
    # verdict-lint.py has a dash in its name, so import it by path.
    spec = importlib.util.spec_from_file_location(
        "verdict_lint", Path(__file__).with_name("verdict-lint.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def transcript_text(path):
    """Assistant text blocks from a session transcript JSONL, joined for linting."""
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            msg = obj.get("message") or {}
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            if isinstance(content, str):
                out.append(content)
            elif isinstance(content, list):
                out.extend(b.get("text", "") for b in content
                           if isinstance(b, dict) and b.get("type") == "text")
    return "\n".join(out)


def run(payload):
    if payload.get("stop_hook_active"):
        return 0  # we already blocked once this stop — never loop the session
    vl = _load_lint()
    problems = []

    tp = payload.get("transcript_path")
    if tp and Path(tp).is_file():
        violations, _seen = vl.lint(transcript_text(tp))
        problems += [f"line {n} [{noun}]: {msg}" for n, noun, msg in violations]

    cwd = Path(payload.get("cwd") or ".").resolve()
    if cwd == PLUGIN_ROOT:  # release check only when developing the plugin itself
        err = vl.release_check(PLUGIN_ROOT)
        if err:
            problems.append(err)

    if problems:
        print("stop-gate: fix before stopping (PROTOCOL §5 form / release consistency):",
              file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 2
    return 0


def selftest():
    import os
    import tempfile
    vl = _load_lint()
    bad = {"message": {"role": "assistant",
                       "content": [{"type": "text", "text": "GATE: passed"}]}}
    ok = {"message": {"role": "assistant",
                      "content": "SLICE login: proven (test executed)"}}

    fd, p = tempfile.mkstemp(suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(bad) + "\n" + json.dumps(ok) + "\n")
        assert run({"transcript_path": p}) == 2, "malformed verdict must block the stop"
        assert run({"transcript_path": p, "stop_hook_active": True}) == 0, \
            "second pass must not loop"
        with open(p, "w", encoding="utf-8") as f:
            f.write(json.dumps(ok) + "\n")
        assert run({"transcript_path": p}) == 0, "clean transcript must pass"
    finally:
        os.unlink(p)

    assert vl.release_check(PLUGIN_ROOT) is None, \
        "plugin's own manifest and CHANGELOG must agree"
    assert vl.release_check(tempfile.gettempdir()) is None, \
        "non-plugin directory must be a no-op"
    print("stop-gate: selftest passed")
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    try:
        return run(json.load(sys.stdin))
    except Exception as e:  # ponytail: fail open — the gate must never wedge a session
        print(f"stop-gate: internal error, passing open: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
