---
name: evolve-maintain
description: >-
  Change a running system without breaking it: upgrades, deprecations, removing an old API, large refactors. Use for "upgrade X", "refactor this module".
disable-model-invocation: true
metadata:
  stage: build
  card: "upgrade, refactor or deprecate on a live system"
---

# Maintenance & Evolution

**Goal:** make the change asked for, and leave every feature that reads what changed doing what it
did before, unless the user asked for that feature to change too. The break to look for is far from
the edit: a command, job or config line that reads the changed name and that no test runs. How you
find the readers and make the change is yours: read it all if it fits, grep, run things. What counts
as done is checked by the helper. `E` is `python <this skill's base directory>/scripts/evolve.py <repo>`.

Run `E` before your first edit: it keeps the tree as it is in `.evolve/before/`. Run `E --gate`
whenever you like; it says which stage is open and what fixes it, and prints the answer once all
three hold (`EVOLVE-GATE: done`).

## The stages

| Stage | Holds when |
|---|---|
| **1. Before** | The tree as it was is kept, and the commands users and jobs run are recorded on it: `E --run "<command>"` runs it in a throwaway copy of the kept tree under a call tracer and records what it prints and every file it writes. It always runs on the tree as it was, so a run added after the edit still records the old behavior. A run that prints something different the second time is refused |
| **2. Reach** | Every function, script or config line that reads a name the change touched (on the tree as it was) was entered by a recorded run, or has `- READER: out: <why the change cannot reach what it does>` in `.evolve/notes.md` (the gate appends the slots). An `out:` that says a run or test covers it is refused: the tracer would have seen that run |
| **3. Hold** | Every recorded command, rerun on the changed tree, prints and writes what it did before. A difference the user asked for gets `- run N: intended: <why>`; any other is a break to fix |

When the cause of a bug is unknown, prove it first (`debug-protocol` does this, if it is
installed). Before deleting anything, show that nothing loads it: `latent-audit` does this if it's
installed. Reverting is a fix. Report the drafted answer with its `[[fill: ...]]` slots filled.
Delete `.evolve/` afterwards.
