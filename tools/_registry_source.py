#!/usr/bin/env python3
"""
_registry_source — one owner for "read the §5 REGISTRY out of a verdict-lint.py
without executing it".

WHY THIS EXISTS
---------------
Two tools need the same thing for two different reasons, and each had grown its own
reader:

  · `registry-check.py` reconciles PROTOCOL §5's table against the linter's dict, and
    must not import the linter (importing executes it, and couples the check to the
    linter's CLI).
  · `stop-gate.py` reads a candidate *checkout's* declared vocabulary under PROTOCOL
    §1's channel-rule carve-out, where executing it is the arbitrary-code-execution
    defect the rule was written for.

Two readers of one declaration can disagree about what a file declares — the regex
version accepted only `REGISTRY = {` at column 0 and split states on commas; this one
asks Python's own parser. That divergence is the rot D-5 documented (six copies of an
encoding guard in two drifted variants), so this is D-5's remedy applied to the second
instance of the same shape: one owner, both callers import it.

WHAT IT DOES NOT OWN
--------------------
The error policy. `registry-check.py` dies on a missing block; `stop-gate.py` fails
closed to {} because a hostile checkout must never wedge the hook. So this returns
`None` for "no parseable REGISTRY here" and lets each caller decide what that means —
the same split `protocol_vintage` makes between *when a check applies* and *what it
decides*.

SAFETY
------
`ast.literal_eval` evaluates literals only: it cannot call, import, or access
attributes. Nothing in this module executes subject code, and nothing in it should
ever be given the power to.

TESTED BY `tools/tests/test_registry_source.py`.
"""

import ast
from pathlib import Path


def read(path):
    """The REGISTRY a `verdict-lint.py` declares, as {noun: {state, ...}}, or None.

    None means "no parseable module-level REGISTRY here" — unreadable file, syntax
    error, no such assignment, or a value that is not a literal dict. Callers
    distinguish that from `{}`, which means "declared, and empty".
    """
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, SyntaxError, RecursionError):
        return None
    for node in tree.body:                      # module level only
        # AnnAssign as well as Assign: `REGISTRY: dict = {...}` is the same
        # declaration, and reading only the bare form would silently miss it.
        if isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        elif isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        else:
            continue
        if value is None:
            continue
        if not any(isinstance(t, ast.Name) and t.id == "REGISTRY" for t in targets):
            continue
        try:
            raw = ast.literal_eval(value)
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            return None
        if not isinstance(raw, dict):
            return None
        return {k: {s for s in v if isinstance(s, str)}
                for k, v in raw.items()
                if isinstance(k, str) and isinstance(v, (set, frozenset, list, tuple))}
    return None
