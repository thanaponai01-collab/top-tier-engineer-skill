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
import ast
import importlib.util
import json
import sys
from pathlib import Path

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
    IMPORTED, executing its module body as the user on every Stop, silently. Identity by
    self-asserted string is not authority (PROTOCOL §9 rule 3: the predicate a gate
    relies on must be the real authority model, not a decorative attribute) — so the
    resolved root may only be READ AS DATA. Code comes from PLUGIN_ROOT alone; see
    `_load_lint`, which takes no root for exactly this reason.
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
    """
    # verdict-lint.py has a dash in its name, so import it by path.
    spec = importlib.util.spec_from_file_location(
        "verdict_lint", PLUGIN_ROOT / "tools" / "verdict-lint.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def registry_from_source(root):
    """The §5 noun→states registry a checkout DECLARES, parsed as data, never executed.

    This is what makes a source checkout's rules govern its own session (`suite_root`
    reason 1 — a session adding a verdict state must be able to stop) without importing
    anything from it. `ast.literal_eval` on the `REGISTRY` assignment evaluates only
    literals: it cannot call, import, or access attributes. Anything unparseable or
    non-literal yields {} — an untrusted checkout can widen the linter's accepted
    vocabulary, which is the same authority it already has by being the code under
    development, and nothing else.
    """
    try:
        src = (Path(root) / "tools" / "verdict-lint.py").read_text(
            encoding="utf-8-sig")
        tree = ast.parse(src)
    except (OSError, ValueError, SyntaxError, RecursionError):
        return {}
    for node in tree.body:                      # module level only
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "REGISTRY"
                   for t in node.targets):
            continue
        try:
            raw = ast.literal_eval(node.value)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            return {}
        if not isinstance(raw, dict):
            return {}
        return {k: {s for s in v if isinstance(s, str)}
                for k, v in raw.items()
                if isinstance(k, str) and isinstance(v, (set, frozenset, list, tuple))}
    return {}


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
    vl = _load_lint()                      # code: install path only, always
    if root != PLUGIN_ROOT:                # doctrine: parsed as data, never executed
        # STRICTLY ADDITIVE, AND ONLY FOR NOUNS THIS RELEASE DOES NOT KNOW.
        # Merging states into an EXISTING noun would let a directory that merely
        # asserts this plugin's name legalise `GATE: passed` and switch the
        # enforcement floor off for a session that is not developing the suite at
        # all. A checkout may teach the gate a noun it has never heard of; it may
        # never loosen a rule the released PROTOCOL already fixed.
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
    # This gate's findings carry the § section mark, and they go to STDERR — which the
    # other tools' stdout-only reconfigure never covered. On Windows stderr defaults to
    # cp1252, so the hook's own output reached the user mojibaked ("PROTOCOL §5" as
    # "PROTOCOL \xa75") and any UTF-8 consumer choked on the byte. Same bug the suite
    # already fixed for stdout in structure-report.py and verdict-lint.py.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass

    if "--selftest" in sys.argv:
        return selftest()
    try:
        return run(json.load(sys.stdin))
    except Exception as e:  # ponytail: fail open — the gate must never wedge a session
        print(f"stop-gate: internal error, passing open: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
