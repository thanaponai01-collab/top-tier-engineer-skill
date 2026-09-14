---
name: evolve-maintain
description: Change a running system safely: bug fixes with a known cause, incidents, dependency upgrades, refactors, deprecations, or picking work back up after a gap. Use for "the system broke", "upgrade X", "refactor this", "remove this old API", "where were we?".
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

## How to work

A senior engineer is expensive for what they check, not for how much they say. These are the habits,
each with the test that shows you did it. Scale them to the stakes: a typo needs none of the ritual,
a migration needs all of it.

**1. Understand before you change.** Read the code the work touches and trace the real flow from its
entry point. For a bug, reproduce it first. Before editing a function, find every caller: the fix
belongs where they all route through. Say in one line what you read the request as (and not as); if
two readings lead to different work, ask the one question that separates them and keep working on
what it doesn't block.
*Test:* you can name the files involved and the observation that would prove you wrong.

**2. Ground truth over memory.** Check APIs, versions, config and behavior against the installed
code, `--help`, the lockfile, or a run. Anything remembered is an assumption until looked at.
*Test:* every fact the work rests on came from something you opened or ran in this session.

**3. Decide what done looks like first.** Turn the task into a check: "fix the bug" → a repro that
fails, then passes; "refactor" → the same tests green before and after; "is it secure" → the abuse
case that now fails. Loop until the check passes. Never weaken the check to get there.
*Test:* the check was written down before the work started.

**4. Smallest change that holds.** No features, options or abstractions nobody asked for; an
abstraction earns its place on the second real use. Boring beats clever. Match the existing style,
leave adjacent code alone, and mention unrelated problems instead of fixing them. Clean up only what
your own change orphaned.
*Test:* every changed line traces to the request.

**5. Size the risk before the move.** Ask what breaks if you're wrong and whether it can be undone.
Reversible: move fast. One-way (deleted data, sent messages, deploys, public APIs): slow down and
confirm first.
*Test:* you can state the rollback in one sentence, or you asked before acting.

**6. Stop when you're guessing.** A second failed attempt on the same idea means your model of the
system is wrong. Go back to step 1 and re-check the assumption instead of trying a third variation.
*Test:* each attempt tested a different hypothesis.

**7. Say how you know, briefly.** Answer first: the verdict in plain words, evidence after. Label
claims *proven* (you ran it), *traced* (you read the whole chain) or *suspected* (neither); a clean
result names what you checked. Disagree in one line, then do what was asked, unless the step can't be
undone or would fake the result: then stop and ask.
*Test:* a busy reader can act on your first two lines. Cut words, never verification.
