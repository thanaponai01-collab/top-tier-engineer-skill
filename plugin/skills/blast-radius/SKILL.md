---
name: blast-radius
description: >-
  Find what a change breaks outside its diff, and prove the one fact it is safe because of. Use for "what else does this break?", "who depends on this?", "is this change safe?"
disable-model-invocation: true
metadata:
  stage: prove
  card: "it works, but what did it break?"
---

# Blast Radius

**Goal:** every consumer of what the change touched, outside the diff, has a verdict, and the one
fact the change is safe because of was run, failing with that fact broken and passing on the
change. How you find the risks is yours: read the callers, follow the names. What counts as done is
checked by the helper. `B` is `python <this skill's base directory>/scripts/blast.py <repo>`.

`B --base <ref>` (the commit the change starts from) lists what the diff changed: Python functions
whose signature, body or existence changed, found by AST, and words the diff no longer writes (a
dict key, JSON field, column, env var, flag) searched by literal name in every tracked text file.
Then every consumer of those outside the diff, signature and removal first. Run `B --gate` whenever
you like; it says which stage is open and what fixes it, drafts the answer once stages 1 and 2
hold, and ends `BLAST-GATE: done`.

## The stages

| Stage | Holds when |
|---|---|
| **1. List** | `.blast/consumers.json` is current with the code. Changed the code since? `B --base <ref>` again |
| **2. Account** | Every listed consumer has a line in `.blast/verdicts.md` (the gate drafts the slots): `- <file:line>: breaks\|cleared\|unknown: <why>`. `breaks` and `cleared` cite the `file:line`, or the library source file:line, they rest on; `unknown` says what it depends on. A consumer outside the repo: `- outside <who>: unknown: <what it depends on>` |
| **3. Fact** | `.blast/fact.md` holds the one fact (`- fact:`, `- cite: <file:line>`), its proof (`` - proof: `<cmd>` ``) and a break: one edit that makes the fact false (`- break: <file>`, `` - old: `<text>` ``, `` - new: `<text>` ``, one line each, `old` unique in the file). The helper runs the proof on a throwaway copy of the change (must pass) and on one with the break applied (must fail). Not needed when a consumer `breaks`: the answer is then `breaks` |

The level in the answer is the highest the helper saw, never one you type: 1 said so, 2 cited a
`file:line` that exists, 3 walked the failure (`- walk:` through two or more such lines), 4 ran
the proof red then green, 5 `B --gate --app "<cmd>"` showed the same in the running app. Below 4
the answer says `unproven`. Look for the fact that clears most consumers at once ("this only drops
entries that are already dead"), not a list of maybes.

Fill the slots of `.blast/answer.md`, then `B --answer-check .blast/answer.md`: it refuses `safe`
below level 4 or with a consumer that breaks, a level above the recorded one, and unfilled slots.
Give that answer.

The product tree is never written: only `.blast/` changes. Report only; fixing what breaks is a
separate task. Commit `.blast/` with the change.
