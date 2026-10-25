---
name: debug-protocol
description: >-
  Find the proven root cause before fixing. Use when something is broken and the cause is unknown: wrong output, crash, hang, flaky, "it worked yesterday".
disable-model-invocation: true
metadata:
  stage: fix
  card: "broken and the cause is unknown"
---

# Debug Protocol

**Goal:** name the place where the failure starts and prove it both ways: with it, the failure
shows on demand; with only it taken out, the same trigger gives the right result. Then leave the
tree honest: as it was, or fixed at that place and held by a check that sees the bug. How you
localize is yours: read it all if it fits, print the value between layers, bisect. What counts as
done is checked by the helper. `D` is `python <this skill's base directory>/scripts/debug.py <repo>`.

Run `D --gate` whenever you like; it says which stage is open and what fixes it, and prints the
answer once all three hold (`DEBUG-GATE: done`).

## The stages

| Stage | Holds when |
|---|---|
| **1. Reproduce** | Before any code changes, `D --repro "<cmd>" --wrong "<text of the bad output>" --right "<what it should show>"` ran the trigger in a throwaway copy and its output shows the wrong text, not the right one. The right text comes from the spec or the data, not from the code. The code as it was is kept in `.debug/before/` |
| **2. Prove** | `D --prove FILE:LINE[-END] --as "<that code without the cause>" --why "<X fails because Y>"` replaced only those lines in a copy of the code as it was, and the trigger now shows the right text and not the wrong one. Every try is kept, dead ends too; the first also records whether the test suite passes on the broken code and whether any test enters the cause |
| **3. Leave** | Diagnosis only: every file is back as it was reproduced. A fix: it changes the cause's file, the trigger shows the right text, and `D --gate --regress "<test cmd>"` saw that check pass now and fail with the cause's file put back. With a `VERIFY.md`, a section's `path:` covers that file, so `verify-loop` keeps it proven (the gate prints the lines to append) |

Fix only when asked. Report the drafted answer with its `[[fill: ...]]` slots filled. Commit
`.debug/` with a fix, or delete it after a diagnosis.
