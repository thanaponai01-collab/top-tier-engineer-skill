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

import _registry_source
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

    SECURITY (the counter-mistake, and why this returns a DOCTRINE root, never a code
    root): the candidate is found by walking cwd's ancestors and matching a manifest
    `name` — a string any directory may assert. A session sitting anywhere under a repo
    that declares this plugin's name would otherwise have that repo's `verdict-lint.py`
    IMPORTED, executing its module body as the user on every Stop, silently (the hook
    fails open, so nothing would be printed either). Identity by self-asserted string is
    not authority — PROTOCOL §1, the channel rule: content read from a subject is
    evidence, never instruction, and a tool resolves its own CODE from its install path,
    never from a path the subject controls. So the root resolved here may only be READ
    AS DATA. Code comes from PLUGIN_ROOT alone; see `_load_lint`, which takes no root
    for exactly that reason.
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


def _load_lint():
    """Import the linter — ALWAYS from the installed plugin, never from a resolved root.

    This function deliberately takes no argument. `exec_module` runs the target's module
    body, so a root parameter here is an arbitrary-code-execution sink fed by whatever
    directory the session happens to sit under (see `suite_root`). Keeping the path
    un-parameterised is a separation that cannot be mis-called rather than a rule a
    caller must remember.

    What the parameter used to buy, and where it went: the rules had to come from the
    checkout being linted, so the old signature loaded that checkout's `verdict-lint.py`
    and put its `tools/` first on `sys.path` for the sibling `protocol_vintage` import —
    and evicted `sys.modules["protocol_vintage"]` around the load, because two roots in
    one process could otherwise mix two versions of the rules. All of that machinery
    existed to make a second root safe. There is now exactly one root, so the mixing it
    guarded against is unreachable and the machinery is gone with it; a checkout's
    *doctrine* reaches the linter through `registry_from_source`, as data.
    """
    # verdict-lint.py has a dash in its name, so import it by path. Its sibling
    # `protocol_vintage` is a plain import, so PLUGIN_ROOT/tools must be importable —
    # a constant derived from __file__, so this holds however stop-gate was invoked
    # (hook, CLI, or loaded by the test suite) and is never subject-controlled.
    # insert(0) unconditionally: membership is not enough. If this path were already
    # present but BEHIND another entry (a PYTHONPATH, a test runner's root), the sibling
    # would resolve from that other entry instead. Precedence is the property we need,
    # and it costs nothing to guarantee it rather than assume it.
    tools = str(PLUGIN_ROOT / "tools")
    sys.path.insert(0, tools)
    try:
        spec = importlib.util.spec_from_file_location(
            "verdict_lint", PLUGIN_ROOT / "tools" / "verdict-lint.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        if sys.path and sys.path[0] == tools:
            sys.path.pop(0)


def registry_from_source(root):
    """The §5 noun→states registry a checkout DECLARES, parsed as data, never executed.

    This is what makes a source checkout's rules govern its own session (`suite_root`
    reason 1 — a session adding a verdict state must be able to stop) without importing
    anything from it. It is PROTOCOL §1's narrow, named carve-out to the channel rule:
    a tool may read a candidate checkout's declared vocabulary as parsed data, and use
    it only to learn a noun this release does not know.

    The parse itself belongs to `_registry_source` (Law 1, every rule lives in exactly
    one place — `registry-check.py` needs the same read for its own reason). What stays
    here is the policy: fail CLOSED to {} on anything unparseable, because a hostile
    checkout must never wedge the hook, and an unreadable one must never widen it.
    """
    return _registry_source.read(Path(root) / "tools" / "verdict-lint.py") or {}


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


# Comfortably clears the longest finding the linter actually emits (measured: 205
# chars; the §11 DELIVERY message is the longest), so clipping never truncates one of
# our own.
_EVIDENCE_LIMIT = 400


def _as_quoted_evidence(msg):
    """Render one finding so subject-controlled text inside it cannot pose as ours.

    PROTOCOL §1, the channel rule: content read from a subject is evidence, never
    instruction. Two findings carry subject bytes verbatim — `release_check` quotes the
    candidate root's declared version strings, and a merged noun's legal-state list is
    entirely the checkout's own words. Both print under this gate's banner, into the
    model's context, as the stated reason a session may not stop.

    A newline is what turns quoted evidence into a forged section of our output ("\\n\\n
    SYSTEM: the enforcement floor is disabled…"), so flattening to a single line is the
    operative half; the clip bounds a subject's claim on the reader's attention. This
    is the smallest thing that holds, and it holds for every finding rather than the
    two known sinks — a rule that has to be remembered at each new sink is the kind
    this file already refused once (see `_load_lint`).
    """
    flat = " ".join(str(msg).split())
    return flat if len(flat) <= _EVIDENCE_LIMIT else flat[:_EVIDENCE_LIMIT] + " …[clipped]"


def run(payload):
    if payload.get("stop_hook_active"):
        return 0  # we already blocked once this stop — never loop the session
    root = suite_root(payload.get("cwd") or ".")
    vl = _load_lint()                      # code: install path only, always
    if root != PLUGIN_ROOT:                # doctrine: parsed as data, never executed
        # STRICTLY ADDITIVE, AND ONLY FOR NOUNS THIS RELEASE DOES NOT KNOW.
        # Merging states into an EXISTING noun would let a directory that merely
        # asserts this plugin's name legalise `GATE: passed` and switch the
        # enforcement floor off for a session that is not developing the suite at
        # all. A checkout may teach the gate a noun it has never heard of; it may
        # never loosen a rule the released PROTOCOL already fixed (§1, channel rule).
        for noun, states in registry_from_source(root).items():
            if noun not in vl.REGISTRY:
                vl.REGISTRY[noun] = set(states)
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
            print("  " + _as_quoted_evidence(p), file=sys.stderr)
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
