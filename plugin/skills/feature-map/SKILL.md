---
name: feature-map
description: >-
  Map features to entry points and checks. Use for "what can this app do, how do I reach X?"
disable-model-invocation: true
metadata:
  stage: orient
  card: "what can this app do, how do I reach X?"
---

# Feature Map

**Goal:** a `FEATURES.md` the next agent reads instead of the code: every feature, the exact way
in, and whether it works, backed by runs the next session can repeat.

How you read, run and write it is yours. What counts as done is checked: `H` is
`python <this skill's base directory>/scripts/features.py`, and `H gate` says which step is open
and what fixes it.

## Steps

| Step | Done when | Checked by |
|---|---|---|
| **1. Inventory** | Every entry point in the code is a feature line or under `## Not features` with its reason, and every feature says what it does, how it gets from entry to effect, and its status | `H gate`: 1 ok |
| **2. Run** | Every command and route was run through `H prove`, passing or failing, or its feature says `traced: <why it was not run>` | `H gate`: 2 ok |
| **3. Hand off** | `AGENTS.md` or `CLAUDE.md` tells the next agent the map is there and how to re-check it | `FEATURE-GATE: done` |

Two lines are not yours to cross: nothing that sends, pays or deletes outside the repo runs
unless the person says so, and anything that writes runs in a copy (`--copy`, `--serve`). Report
the `Proof:` line the gate prints.

## Tools

- `H init`: drafts `FEATURES.md` from the entry points in the code, in the format the checker reads.
- `H prove --feature "<name>" [--copy] -- <command>`: runs a command and keeps the receipt.
- `H prove --feature "<name>" --serve "<start cmd with {port}>" --request "GET /path" [--entry "click: <anchor>"]`:
  runs a web route in a throwaway copy; a page control whose code sends that request is proven with it.
- `H gate`: the three steps, what is open, the fix for each problem.
- `python .features/features.py check --rerun`: the vendored alarm for later sessions; `prove --again` re-records.
