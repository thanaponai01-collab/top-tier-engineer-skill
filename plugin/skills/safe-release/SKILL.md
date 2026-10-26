---
name: safe-release
description: >-
  Deploy, or change stored data, with a proven way back. Use for "deploy", "ship it", "push to prod", "migration", "alter table", "backfill".
disable-model-invocation: true
metadata:
  stage: ship
  card: "deploy, or change the shape of stored data"
---

# Safe Release

**Goal:** say whether the release can go out (ship, stage or hold), and give a way back that was
run, not guessed. The change and its way back are rehearsed on copies of the live data, with the code
that runs today as well as the changed code, because today's code keeps running on the new data
between the migration and the restart, and again after a code-only revert. Data is what a revert
cannot bring back, so every loss is named with the step that causes it. The live data is never
written; running the release is its owner's call. How you read the change and choose its shape is
yours. What counts as done is checked by the helper. `R` is
`python <this skill's base directory>/scripts/release.py <repo>`.

Run `R` once before you change anything (without git it keeps the tree as today's code). Run
`R --gate` whenever you like; it says which stage is open and what fixes it, and prints the answer
once all three hold (`RELEASE-GATE: done`).

## The stages

| Stage | Holds when |
|---|---|
| **1. Forward** | `R --rehearse --forward "<cmd>" --back "<cmd>" --probe "<cmd>"` ran on the current tree. On a copy of the live data the forward step passes and is safe to run twice, the changed code's probes pass, and at least one probe writes the way the product does. Probes are commands that use the data through the code (keep them in `.release/probes/`); each also passes on today's code and today's data. Every constraint the forward step drops is kept, or named with `- DROPS <what>: <why>` in `.release/plan.md`. The helper prints the rows that changed: read them |
| **2. Back** | Today's code (git `HEAD`, or `--old REF|DIR`) passes its probes on the migrated data, or the plan closes that window with `WINDOW: <how no old code runs on the new data>`. The back step runs after forward, and gives the data back row for row, or each loss is named with `- LOSES <what>: <the step after which it is gone>` |
| **3. Call** | `.release/plan.md` fills `CALL` (ship, stage or hold), `ROLLBACK` (the rehearsed back step, in order), `NO-RETURN`, `WATCH`, and one `- CARRIES` line for each changed file that runs in production (the gate appends the slots). The live data is as it was at the first `R` |

Make the change only when asked; otherwise rehearse what is there and report. An external action
(an email, a charge, a deletion, a public API) needs the owner's explicit grant for that action.
Report the drafted answer with its `[[fill: ...]]` slot filled. Delete `.release/` afterwards, or
commit it with the change.
