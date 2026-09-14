---
name: evolve-maintain
description: >
  Change a running system safely: bug fixes with a known cause, incidents, dependency upgrades, refactors, deprecations, or picking work back up after a gap. Use for "the system broke", "upgrade X", "refactor this", "remove this old API", "where were we?".
---

# Maintenance & Evolution

A running system has a history and a future; it's not a blank page. Classify every change before
making it, size it by how far it reaches, prove it like new work, and leave the system harder to
break the same way twice.

## Phases

### 1. Sense
Establish what's true before touching anything:
- Reproduce the reported behavior, or say clearly that you couldn't and what you inferred.
- If it reproduces but the cause is unknown, diagnose first: prove the cause (present → fails,
  removed → doesn't) before treating it. Treating an unproven cause is symptom-patching.
- Read project notes and recent commits. Symptoms often trace to an assumption that quietly stopped
  being true, or a TODO whose moment came and went.
- **Drift check:** do the docs still describe the code? Stale docs are a finding; the next reader
  will build on them.

### 2. Triage
| Class | Meaning | Obligations |
|---|---|---|
| **Fix** | Restore intended behavior | Root cause named, regression test added, prevention step (Phase 4) |
| **Adapt** | The world changed (dependency, API, OS) | Diff the compatibility surface before upgrading; pin and schedule if not now |
| **Migrate** | Stored data changes shape | Expand → backfill → verify → contract, with a backward path. Never change a populated schema in place |
| **Improve** | Same behavior, better structure | Freeze behavior with tests *before* refactoring; success = zero observable change |
| **Evolve** | New or changed behavior | Define acceptance criteria first. Maintenance is not permission to grow scope |

Then size **how far it reaches**: modules, contracts, data, callers. Short reach → one direct
change. Long reach → staged, using the deprecation ladder. A "small fix" that reaches far was
misclassified.

### 3. Treat
- Small, proven increments: build, wire, run the proof, commit. Quick fixes get no exemption; most
  rot in old code is what quick fixes left behind.
- **Cause, not symptom.** A fix is done when you can name the cause and why it wasn't caught earlier
  (no test, a guard never connected, a false assumption).
- **Code that looks wrong but predates you:** check git history first. If there's a reason, respect
  it or explicitly replace it. If there's none, proceed with extra proof, not extra confidence.
- **Deprecation ladder** for removing anything with callers: mark → warn → move callers → remove,
  counting remaining callers at each step (code search is traced; runtime evidence is proven, use
  it where possible).
- **Reverting is always a legitimate fix.** A clean revert beats a clever fix forward when unsure.

### 4. Strengthen
- Every Fix produces a regression test and, where the same kind of failure could happen elsewhere, a
  new invariant or contract change, so the whole class of bug dies.
- If reproducing was hard, add the log, metric or probe that would have made it easy, in the same
  change.
- On periodic health checks: close stale TODOs, confirm or drop old assumptions, fix doc drift.

### 5. Record
If the project keeps a maintenance log, append:
`date | class | symptom | root cause | treatment | reach | guarded by | follow-ups`.
Write it so a future symptom can be matched to past causes in one read.

## Report

The symptom in the reporter's words, the root cause in one sentence (proven or traced), what now
stops it coming back, and anything left for later.

## Common mistakes

Deleting code something still calls; stale docs misleading the next maintainer; scope growth
disguised as maintenance; closing a fix with no regression test.
