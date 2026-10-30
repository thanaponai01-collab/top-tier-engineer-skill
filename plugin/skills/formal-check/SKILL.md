---
name: formal-check
description: >-
  Prove a property for every case, not just the ones tested, and keep that proof true to the code. Use for races, retries, state machines, parsers or unsafe code where tests miss the case that breaks: "model-check this", "prove this invariant", "can these steps happen in a bad order?", "is the model still true to the code?"
disable-model-invocation: true
metadata:
  stage: prove
  card: "tests pass, but every order of steps?"
---

# Formal Check

**Goal:** one promise of the code, where a break harms users and tests rarely reach the case that
breaks it, is checked for every case in a stated scope. The check passes on the code and fails
with the guarded code broken, every part of its model points at a line that exists, and it goes
stale the moment the covered code changes. Choosing the target, the tool and the model is yours.
What counts as done is checked by the helper.
`F` is `python <this skill's base directory>/scripts/formal.py <repo>`.

`F --scan` lists candidates in `.formal/candidates.md` (locks, threads, retries, state fields,
parsers, unsafe code). Pick the promise whose break costs the most, not the easiest to verify.
Pick the tool the question needs: whether steps can happen in a bad order suits a model checker
over a small model (TLA+ by default, any language); whether the code behaves for every input suits
a verifier that runs on the code (Kani, CBMC, Dafny, CrossHair) or, when none runs on this
language, generated inputs against the real code (Hypothesis, fast-check). The tool is the repo's
dependency. To the helper a check is a command: exit 0 when the property holds.

Write `.formal/<name>.md` (`F --gate` prints the fields), then run `F --gate` whenever you like;
it says which stage is open and what fixes it, drafts `.formal/answer.md`, and ends
`FORMAL-GATE: done`.

## The stages

| Stage | Holds when |
|---|---|
| **1. Record** | `property` and `harm` (one plain sentence each), `target` (a `file:line`), `tool` with its version, `` cmd: `<command>` ``, `model`, `covers`, `bounds`, `assumes` are all there, and the files exist |
| **2. Map** | Each `- map: <model element> -> <file:line>` names text in the model and a line that exists in a `covers` file; every covered path has a map line. What the model treats as one step is one step in the code |
| **3. Run** | `cmd` passes on a throwaway copy of the working tree within the budget (600 s; `--budget`). A failure is a finding, never a reason to weaken: two or more `- step: <what happens> <file:line>` lines tell it in the code's words, and the outcome is `bug`. A missing tool is `blocked`. With CI config, the same command runs there |
| **4. Break** | `- break: <covered file>`, `` - old: `<text>` `` (once in the file), `` - new: `<text>` ``: one edit to the code, never the model, that makes the property false. `cmd` must fail with it applied, or it cannot fail |
| **5. Sync** | On its first green run the gate locks `property`, `bounds` and `assumes` and the sync commit in `.formal/<name>.lock`. Changing them later needs `- changed: <old> -> <new> evidence: <sha\|file:line>`. A commit to covered code since the sync makes the check `stale` until `F --drift` lists it and `.formal/<name>.drift.md` classifies it: `- <sha>: no-effect\|reshaped\|promise-changed\|suspect: <why>` (`promise-changed` cites `evidence:`) |

Update a stale model from the code before you rerun, not from what makes it pass. A pass after an
update proves nothing until the break fails again; a failure after one is drift if a step cannot
happen in the code, and a bug if every step can. Renamed covered files are followed: update
`covers` and the map lines. Only the gate moves the sync commit, after a green run with the break
red and the covered files committed.

Outcomes, set by the gate: `in-sync`, `updated`, `bug`, `blocked`, `stale`. Fill the slots of
`.formal/answer.md`, then `F --answer-check .formal/answer.md`: it refuses an outcome the gate did
not record, a check it never saw, and unfilled slots. Say what was verified, with which tool and
why, under which bounds and assumptions, and what it does not cover. A pass covers the model or the
bound, not the whole system.

The helper never writes the product tree: commands run in throwaway copies, and only `.formal/`
changes. Commit `.formal/` so the next agent reruns `F --gate` on every change to covered code. A
bug goes to debug-protocol or the user; this skill does not fix product code.
