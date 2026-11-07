---
name: untangle
description: >-
  Untangle a codebase where its history says changes hurt, keeping behavior the same. Use for "untangle this", "clean up the structure so the next change is easier".
disable-model-invocation: true
metadata:
  stage: change
  card: "untangle it where changes hurt"
---

# Untangle

**Goal:** the next person to change this code, most likely an agent, spends less effort finding
what to change, breaks less without noticing, and finds a bug's cause faster. What the program does
stays the same. Untangle where the history says changes land and fixes repeat. A tangle that is
easy to see but that nothing ever changes is not the target. How you read the code and what you move
are yours. What counts as done is checked by the helper. `U` is
`python <this skill's base directory>/scripts/untangle.py <repo>`; it needs git.

`U` alone ranks the files that change most and get fixed most, the pairs of files that keep changing
together, and the fix subjects behind each. A file untouched in the last 100 commits is not ranked.
Run `U --gate --run "<test cmd>" ...` whenever you like. It says which stage is open and what fixes
it, appends the slots it needs to `.untangle/notes.md`, and prints the answer once all three hold
(`UNTANGLE-GATE: done`). A guard or suite run is reused while the code is unchanged, so rerunning the
gate after editing only the notes is cheap.

## The stages

| Stage | Holds when |
|---|---|
| **1. Baseline** | Before any code changed, `--run` recorded every test command on the tree as committed, and each command ran tests (a command that ran none, or printed no count and failed, is refused and nothing is recorded). Every ranked hotspot and pair has `target: <the commits that show what it costs>` or `skip: <why it does not hurt>`. Fixes repeated in one file are a tangle inside that file: a `FIX-HEAVY` hotspot (a third or more of its commits are fixes) can be skipped only with `\| guard: <cmd>`, run by the gate, that names a test file mentioning that module. Every red test (one slot per file and failure message) has `env`, `stale` or `bug`, with its evidence. A `bug` names the `file:line` of the fault and has a `untangle: known bug: <symptom>` comment within 3 lines of it, where the next person debugging will look. A test that is red because of a real fault is a bug, not a stale test |
| **2. Untangle** | Every changed code file is a target, or has `- also <file>: serves <target>`; a file whose only change is a bug comment needs neither. Every target has `- move <target>: <what changed> \| guard: <cmd>` (or `guard: none: <why>`, or `not moved: <why>`). A targeted pair takes one move, `- move <a> + <b>: ...`, for both files. A move whose files did not change is refused. A guard passes now and fails on the committed tree, with its test files copied in, so it catches the tangle coming back |
| **3. Same behavior** | The same `--run` commands on the changed tree: no test that was green at the baseline is red, and no command ran fewer tests |

Don't fix a `bug` red as part of the untangle; it changes behavior. Name it first in the answer.
Commit `.untangle/` with the change, or delete it.
