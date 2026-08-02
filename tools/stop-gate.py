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

from _encoding import utf8_streams

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def _manifest_name(root):
    """The plugin name a directory declares, or None if it declares none."""
    try:
        return json.loads((Path(root) / ".claude-plugin" / "plugin.json")
                          .read_text(encoding="utf-8-sig"))["name"]
    except (OSError, KeyError, ValueError):
        return None


def suite_root(cwd):
    """The suite whose RULES govern this session — the checkout being edited if there
    is one, else the installed plugin.

    Why this is not just PLUGIN_ROOT: the hook runs from wherever the plugin is
    INSTALLED (a pinned version cache), while a session developing the suite is editing
    a source checkout somewhere else. Resolving from `__file__` alone caused two real
    failures, both found by this suite's own v1.15.0 work:

      1. A session that ADDS a verdict state could never stop. Its transcript emits the
         new state, the installed release's registry does not know it yet, and the gate
         blocks — so the change cannot be finished until it is released, and it cannot
         be released until it is finished. The suite must be lintable by the rules it
         is currently writing, or it can never grow a verdict noun again.
      2. The release check (plugin.json vs CHANGELOG, added v1.14.1) was inert in the
         hook path: it only fires when `cwd == PLUGIN_ROOT`, and under the hook those
         are never equal. It had been silently checking nothing.

    Both are the same mistake — trusting where the code lives over what the session is
    working on.
    """
    # Identity comes from the manifest, never from a directory name: the install path
    # is <plugin>/<version>/ and the source checkout is named top-tier-engineer-skill,
    # so neither directory is called what the plugin is called.
    mine = _manifest_name(PLUGIN_ROOT)
    if mine is None:
        return PLUGIN_ROOT
    try:
        here = Path(cwd).resolve()
    except (OSError, ValueError):
        return PLUGIN_ROOT
    for cand in (here, *here.parents):
        if (cand / "tools" / "verdict-lint.py").is_file() \
                and _manifest_name(cand) == mine:
            return cand
    return PLUGIN_ROOT


def _load_lint(root=PLUGIN_ROOT):
    # verdict-lint.py has a dash in its name, so import it by path.
    tools = str(Path(root) / "tools")
    # verdict-lint imports its sibling `protocol_vintage` (the §11 rule-vintage owner).
    # `root` may differ from this file's own root — the rules must come from the checkout
    # being linted — so that checkout's tools/ goes FIRST on sys.path, or the sibling would
    # resolve to the *running* plugin's copy and mix two versions of the rules.
    #
    # sys.path ALONE is not enough: `sys.modules` is consulted before any path search, so a
    # second load from a different root silently reuses the first root's module. One
    # `_load_lint` per process makes that unreachable today, but `selftest()` already calls
    # this five times, so the cache is evicted around the load and restored after. (Proven by
    # the v1.17.0 scrutinize gate, which reproduced the mix with a synthetic second checkout.)
    cached = sys.modules.pop("protocol_vintage", None)
    sys.path.insert(0, tools)
    try:
        spec = importlib.util.spec_from_file_location(
            "verdict_lint", Path(root) / "tools" / "verdict-lint.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        if sys.path and sys.path[0] == tools:
            sys.path.pop(0)
        if cached is not None:
            sys.modules["protocol_vintage"] = cached
        else:
            sys.modules.pop("protocol_vintage", None)


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
    root = suite_root(payload.get("cwd") or ".")
    vl = _load_lint(root)
    problems = []

    tp = payload.get("transcript_path")
    if tp and Path(tp).is_file():
        violations, _seen = vl.lint(transcript_text(tp))
        problems += [f"line {n} [{noun}]: {msg}" for n, noun, msg in violations]

    if root != PLUGIN_ROOT:  # a source checkout of the suite: check its release state
        err = vl.release_check(root)
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

    # Root resolution: the rules that govern a session come from the checkout it is
    # editing, not from wherever the hook script happens to be installed. Regression
    # guard for the two failures documented on suite_root().
    assert suite_root(PLUGIN_ROOT / "tools") == PLUGIN_ROOT, \
        "a path inside the suite must resolve to the suite root"
    assert suite_root(tempfile.gettempdir()) == PLUGIN_ROOT, \
        "an unrelated directory must fall back to the installed plugin"
    assert _manifest_name(PLUGIN_ROOT) is not None, \
        "the plugin must declare a name for root resolution to key on"
    print("stop-gate: selftest passed")
    return 0


def main():
    utf8_streams()

    if "--selftest" in sys.argv:
        return selftest()
    try:
        return run(json.load(sys.stdin))
    except Exception as e:  # ponytail: fail open — the gate must never wedge a session
        print(f"stop-gate: internal error, passing open: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
